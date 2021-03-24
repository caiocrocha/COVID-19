# Select all deu erro
# Mostrar distribuicao dos dados para descritores (n < 10)
# Build pipeline: escolher classificador antes
# Mostrar tabela de metricas (para os modelos progressivamente)

# Usar postera inteiro como conjunto de treinamento (opcao, elimina teste)
# Upload dados de treinamento, teste (generalizacao)

# Colocar opcao de usar descritores otimos (se selecionado rdkit) de acordo com o classificador
# Otimizar: calculo dos descritores para os novos dados (new_data)

# Opcoes: baixar resultados e baixar modelo pickle
# Colocar SelectKBest com escolha de K

# Escrever requirements, adicionar mordred e rdkit

#show labeled compounds ser mais claro
#modelo foi lido do pickle
#incluir depois da curva roc metricas de avalacao
#explicar treinamento e teste

import os
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib import pyplot

from rdkit import Chem
from rdkit.ML.Descriptors.MoleculeDescriptors import MolecularDescriptorCalculator

# Program
class App():
    def __init__(self, DATA_URL):
        # Show logo, title and description
        self.show_logo()
        self.show_description()
        # Create .metadata directory
        self.create_metadata_dir()

        ########################
        # Load Activity data 
        ########################
        st.markdown('## **Activity data**')
        st.markdown('### Visualizing properties')
        self.downloaded_data = self.download_activity(DATA_URL)
        self.write_smiles(self.downloaded_data, '.metadata/smiles.smi')

        #######################
        # Summary of the data 
        #######################
        self.data = self.downloaded_data.copy()
        self.activity_label = None
        self.show_properties() # show properties and set activity label
        self.label_compounds() # drop activators and label the compounds according to their activity

        #######################
        # Load descriptors 
        #######################
        self.calc = None
        self.descriptors = self.calculate_descriptors()
        self.merged_data = None
        
        #######################
        # ML 
        #######################
        self.new_data = None
        self.pipeline = None
        self.X_train  = None
        self.X_test   = None
        self.y_train  = None
        self.y_test   = None
        self.test_proba  = None
        self.train_proba = None
    
    # Functions
    @staticmethod
    def show_logo():
        st.sidebar.image('logo/Logo_medium.png')

    @staticmethod
    def show_description():
        st.markdown('''## **Welcome to**
# SARS-CoV-2
## Machine Learning Drug Hunter
A straightforward tool that combines experimental activity data, molecular descriptors and machine 
learning for classifying potential drug candidates against the SARS-CoV-2 Main Protease (MPro).     

We use the **COVID Moonshot**, a public collaborative initiatiave by **PostEra**, as the dataset of 
compounds containing the experimental activity data for the machine learning classifiers. We'd like 
to express our sincere thanks to PostEra, without which this work wouldn't have been possible.    

The molecular descriptors can be automatically calculated with Mordred or RDKit, or you can also 
provide a CSV file of molecular descriptors calculated with an external program of your preference.     

This main window is going to guide you through the App, while the sidebar to the left offers you an extra 
interactive experience with options that allow more control over the construction of the Pipeline. **Let's get started!**
''')

    @staticmethod
    def create_metadata_dir():
        if not os.path.isdir('.metadata'):
            os.mkdir('.metadata')
    
    @staticmethod
    @st.cache(suppress_st_warning=True, allow_output_mutation=True)
    def download_activity(DATA_URL):
        # Verbose
        st.text('Fetching the data from PostEra...')
        data_load_state = st.markdown('Loading activity data...')
        data = pd.read_csv(DATA_URL)
        data.to_csv('activity.csv', index=False)
        st.text('Data saved to "activity.csv"')
        return data
    
    @staticmethod
    @st.cache(suppress_st_warning=True, allow_output_mutation=True)
    def write_smiles(data, smiles):
        # Write smiles to disk
        data[['SMILES','CID']].to_csv(smiles, sep='\t', header=None, index=False)

    @staticmethod
    @st.cache(suppress_st_warning=True)
    def write_mordred_descriptors(smiles, csv):
        # Run MORDRED with smiles file.
        # Could not make mordred work with rdkit.
        # There is a lot of (unsolved) confusion with library compatibility
        # Let's rely on the manual way
        if os.path.isfile(smiles) and not os.path.isfile(f'{csv}.gz'):
            os.system(f'python -m mordred {smiles} > {csv}')

        if os.path.isfile(csv):
            os.system(f'gzip {csv}')
    
    @st.cache(suppress_st_warning=True)
    def write_rdkit_descriptors(self, smiles, csv):
        if os.path.isfile(smiles) and not os.path.isfile(f'{csv}.gz'):
            # Get molecules from SMILES
            mols = [Chem.MolFromSmiles(i) for i in self.data['SMILES']]

            # Get list of descriptors
            descriptors_list = [a[0] for a in Chem.Descriptors.descList]

            calculator = MolecularDescriptorCalculator(descriptors_list)
            calc_descriptors = [calculator.CalcDescriptors(m) for m in mols]
            
            descriptors = pd.DataFrame(calc_descriptors, columns=descriptors_list)
            descriptors.insert(0, column='CID', value=self.data['CID'])
            descriptors.to_csv(f'{csv}.gz', index=False, compression='gzip')

    def calculate_descriptors(self):
        st.markdown("## **Descriptors**")
        if st.checkbox('Calculate Mordred descriptors'):
            self.write_mordred_descriptors('.metadata/smiles.smi', '.metadata/csv/mordred.csv')
            # Read MORDRED descriptors
            descriptors = pd.read_csv('.metadata/csv/mordred.csv.gz', compression='gzip')
            descriptors.rename(columns={'name':'CID'}, inplace=True)
            self.calc = 'mordred' # control variable
        elif st.checkbox('Calculate RDKit descriptors'):
            self.write_rdkit_descriptors('.metadata/smiles.smi', '.metadata/csv/rdkit.csv')
            # Read RDKit descriptors
            descriptors = pd.read_csv('.metadata/csv/rdkit.csv.gz', compression='gzip')
            self.calc = 'rdkit' # control variable
        else:
            file = st.file_uploader('or Upload descriptors file')
            show_file = st.empty()

            if not file:
                show_file.info("Please upload a file of type: .csv")
                st.stop()
            else:
                descriptors = pd.read_csv(file)
                if not 'CID' in descriptors.columns:
                    st.error('Compounds must be identified by "CID"')
                    st.stop()
            file.close()
            self.calc = 'other' # control variable
        
        st.dataframe(descriptors.head())

        descriptors_list = descriptors.columns.tolist()[1:]
        selected = st.multiselect(label="Select descriptors", options=(
            ['Select all ({})'.format(len(descriptors_list))] + descriptors_list))
        if 'Select all ({})'.format(len(descriptors_list)) in selected:
            selected = descriptors_list
        st.write("You have selected", len(selected), "features")

        if not selected:
            st.stop()
        
        descriptors = descriptors[['CID'] + selected]
        return descriptors
        
    def show_properties(self):
        # List numeric columns
        data_numeric = self.data.select_dtypes(include=[int,float]).columns.tolist()
        if 'activity' in data_numeric:
            data_numeric.remove('activity')

        ########################
        # Explore data
        ########################

        # Create a sidebar dropdown to select property to show.
        activity_label = st.sidebar.selectbox(label="Filter by: *",
                                        options=([None, *data_numeric]))
        st.sidebar.markdown('''\* _The classifier will be trained according to the selected property. 
If no property is selected, then **f_inhibition_at_50_uM** will be used for labeling the compounds.    
A compound will be considered active if the **`Selected Property > 50`**. This value can be adjusted with the slider below._''')
        
        if activity_label is None:
            activity_label = 'f_inhibition_at_50_uM'

        self.activity_label = activity_label

        # Create a sidebar slider to filter property
        ## Step 1 - Pick min & max for picked property 
        max_val  = float(self.data[activity_label].max())
        min_val  = float(self.data[activity_label].min())
        #mean_val = float(self.data[activity_label].mean())

        ## Step 2 - Create the sidebar slider
        min_filter, max_filter = st.slider("Filter by: " + activity_label, 
                                min_val,
                                max_val,
                                (min_val, max_val))
        
        df_properties = self.data[['CID', activity_label]].dropna()
        df_filtered = df_properties[df_properties[activity_label].between(
            float(min_filter), float(max_filter))]
        mean_filter = float(df_filtered[activity_label].mean())

        st.markdown(f'''
        | Property | Min | Max | Mean |
        | --- | --- | --- | --- |
        | {activity_label} | {min_filter:2g} | {max_filter:2g} | {mean_filter:2g} |

        ''')

        st.text('')
        if st.checkbox('Show downloaded data'):
            st.dataframe(self.downloaded_data)

    def label_compounds(self):
        threshold = st.sidebar.slider("Threshold for selecting active compounds:", 0, 100, value=50)

        # Plot the distribution of the data
        dist = self.downloaded_data[['CID', self.activity_label]].copy()
        dist['activity'] = 'inhibitor'
        dist.loc[dist[self.activity_label] <= threshold, 'activity'] = 'inactive'
        dist.loc[dist[self.activity_label] < 0, 'activity'] = 'activator'

        if not st.checkbox('Hide graph'):
            fig, ax = pyplot.subplots(figsize=(15,5))
            sns.histplot(data=dist, x='f_inhibition_at_50_uM', hue='activity', ax=ax)
            pyplot.ylabel('Number of compounds')
            pyplot.title('Distribution of the data')
            st.pyplot(fig)
        
        self.data.dropna(subset=[self.activity_label], inplace=True)
        self.data = self.data.query(f'{self.activity_label} > 0') # Drop activators (negative inhibition)

        # Label the compounds
        self.data['activity'] = 0
        self.data.loc[self.data[self.activity_label] > threshold, 'activity'] = 1

        st.write('Note: All **activators** have been removed from the dataset, and the **inhibitors** will be referred as **active** compounds.')
        # Create sublists
        actives    = self.data.query(f'{self.activity_label} > {threshold}')
        inactives  = self.data.query(f'{self.activity_label} <= {threshold}')

        st.markdown(f'''
        |Compounds|Active|Inactive|
        |---|---|---|
        |{len(self.data)}|{len(actives)}|{len(inactives)}|
        ''')
        
    def merge_dataset(self):
        # Merge the dataset to include activity data and descriptors.
        merged_data = pd.merge(self.data[['CID', self.activity_label, 'activity']].dropna(), 
                            self.descriptors, on=['CID'])
        # Write Merged Dataset
        if not os.path.isfile('.metadata/csv/merged.csv'):
            merged_data.to_csv('.metadata/csv/merged.csv', index=False)

        return merged_data

    def calculate_cross_corr(self):
        X = self.merged_data.drop(['CID','activity'], axis=1).dropna(axis=1)
        Y = self.merged_data[self.activity_label]
        corr = X.corr()
        st.write(corr.head(5))

        if st.checkbox('Show entire DataFrame'):
            if len(corr) <= 100:
                st.write(corr)
            else:
                st.error("Sorry, large DataFrames can't be displayed!")

        if st.checkbox('Show correlation HeatMap'):
            if len(corr) <= 100:
                fig, ax = pyplot.subplots(figsize=(10,10))
                sns.heatmap(corr, annot=True, cmap='Reds', square=True, ax=ax)
                st.pyplot(fig)
            else:
                st.error("Sorry, large DataFrames can't be displayed!")

        if st.checkbox('Remove highly correlated features (|Correlation| > Correlation Threshold)', True):
            value = st.slider('Correlation Threshold', 0.0, 1.0, value=0.95)

            # https://chrisalbon.com/machine_learning/feature_selection/drop_highly_correlated_features/
            # Create correlation matrix
            corr_matrix = corr.drop([self.activity_label], axis=1).abs()
            # Select upper triangle of correlation matrix
            upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))

            # Find features with correlation greater than "value"
            to_drop = [column for column in upper.columns if any(upper[column] > value)]

            # Drop features 
            st.write('Removed features: ')
            st.write(to_drop)
            self.descriptors.drop(to_drop, axis=1, inplace=True)
            self.merged_data.drop(to_drop, axis=1, inplace=True)

    def calculate_pca(self):
        descriptors_list = self.descriptors.columns.tolist()[1:]
        max_value = len(descriptors_list)
        default = 0.9
        n_components = st.number_input(f'Please enter the number of components to select [0, {max_value}]: ', 
                        value=default, min_value=0.0, max_value=float(max_value))
        st.markdown(f'''\* If the input number is less than 1, then it will correspond to the percentage of the explained 
variance. E.g. the default value corresponds to an explained variance of {default * 100}%.''')
        if n_components > 1:
            n_components = int(n_components)

        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler()
        # Split training set into X and y
        y = self.merged_data['activity']
        X = self.merged_data[descriptors_list].copy()
        # Apply StandardScaler on X
        X_transformed = scaler.fit_transform(X)
        X = pd.DataFrame(X_transformed, columns=X.columns.tolist())

        state = st.text('Running PCA...')
        # Fit and transform the training data
        pca = PCA(n_components=n_components)
        X_pca = pca.fit_transform(X)

        state.text('PCA completed!')
        variance_total = sum(pca.explained_variance_ratio_)
        if pca.n_components_ < 51:
            fig, ax = pyplot.subplots(figsize=(12,4))
            sns.barplot(x=[i for i in range(1, pca.n_components_ + 1)], y=pca.explained_variance_ratio_, ax=ax)
            ax.set(xlabel='Principal Component', ylabel='Explained variance ratio', 
                                    title=f'Variance explained by {variance_total * 100:.1f}%')
            st.pyplot(fig)
        else:
            st.write(f'Explained variance: {variance_total * 100:.1f}%')

        # Reassign the data to the new transformed data
        pca_data = pd.DataFrame(X_pca)
        pca_features = [f'PCA_{i:02d}' for i in range(1, pca.n_components_ + 1)]
        pca_data.columns = pca_features
        pca_data['CID'] = self.merged_data['CID'].tolist()
        pca_data['activity'] = y.tolist()
        # Rearrange the columns
        cols = pca_data.columns.tolist()
        cols = cols[-2:] + cols[:-2]
        pca_data = pca_data[cols]

        self.merged_data = pca_data
        self.descriptors = pca_data[['CID'] + pca_features]
        st.write('### Extracted features')
        st.write(self.descriptors.head())
        st.write('These features are going to be the input data for the model.')

    def feature_selection(self):
        st.markdown('# Feature selection')
        st.markdown('Filter the selected descriptors. The steps bellow are applied sequentially.')

        st.markdown('## Cross Correlation')
        if st.checkbox('Compute the cross correlation between the features'):
            self.calculate_cross_corr()

        st.markdown('## PCA')
        if st.checkbox('Calculate PCA of the selected features'):
            self.calculate_pca()
        
        if st.checkbox('Show histogram plots of the selected features'):
            descriptors_list = self.descriptors.columns.tolist()[1:]
            tmp = pd.melt(self.descriptors, id_vars=['CID'], value_vars=descriptors_list[:12])
            g = sns.FacetGrid(data=tmp, col='variable', col_wrap=4, sharey=False, sharex=False)
            g.map(sns.histplot, 'value')
            if len(descriptors_list) > 11:
                st.warning("""Unfortunately, we can't plot all selected descriptors    
Showing the distribution plots of the top 12 features""")
            st.pyplot(g)
            
    @staticmethod
    def select_model():
        model_list = ['RandomForestClassifier', 'XGBClassifier', 'KNeighborsClassifier']
        model_name = st.sidebar.selectbox(label="Classifier", options=(model_list))

        st.sidebar.markdown('''Note: The hyperparaters showed bellow are the optimal parameters found in our study. 
Nevertheless, feel free to change them as you will.''')
        if model_name == 'RandomForestClassifier':
            from sklearn.ensemble import RandomForestClassifier

            n_estimators = st.sidebar.slider("Number of Estimators", 0, 1000, value=1000)
            max_depth = st.sidebar.slider("Maximum depth per Tree", 0, 10, value=8)
            return (model_name, RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=13))

        elif model_name == 'XGBClassifier':
            from xgboost import XGBClassifier

            n_estimators = st.sidebar.slider("Number of Estimators", 0, 1000, value=200)
            max_depth = st.sidebar.slider("Maximum Depth per Tree", 0, 10, value=3)
            eta = st.sidebar.slider("Learning Rate (ETA)", 0.0, 1.0, value=0.1)
            return (model_name, XGBClassifier(objective='reg:logistic', n_estimators=n_estimators, 
                max_depth=max_depth, eta=eta, random_state=13))

        else:
            from sklearn.neighbors import KNeighborsClassifier

            n_neighbors = st.sidebar.slider("Number of Neighbors", 0, 10, value=5)
            return (model_name, KNeighborsClassifier(n_neighbors=n_neighbors))

    def split_X_and_y(self):
        from sklearn.model_selection import train_test_split
        X = self.merged_data[self.descriptors.columns[1:]]
        y = self.merged_data['activity']
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                                            X, y, test_size=0.2, random_state=27)

    @st.cache(suppress_st_warning=True)
    def mlpipeline(self, model_name, model):
        from sklearn.preprocessing import StandardScaler
        from imblearn.over_sampling import SMOTE
        from imblearn.pipeline import Pipeline
        
        self.pipeline = Pipeline(steps=[('smote', SMOTE(random_state=42)), 
                                        ('scaler', StandardScaler()), 
                                        ('clf', model)
                                        ])
        self.pipeline.fit(self.X_train, self.y_train)

        import pickle
        # Serialize model
        if not os.path.isdir('pickle'):
            os.mkdir('pickle')
        with open(f'pickle/{model_name}.pickle', 'wb') as file:
            pickle.dump(self.pipeline, file)

        features = list(self.descriptors.columns[1:])
        # Save input features names
        with open('.metadata/features.lst', 'w+') as features_file:
            features_file.write("\n".join(features))
    
    def train_test_proba(self, model_name):
        import pickle
        try:
            file = open(f'pickle/{model_name}.pickle', 'rb')
            self.pipeline = pickle.load(file)
            file.close()
        except OSError as e:
            st.error("Oops! It seems the model hasn't been trained yet. Error traceback: ")
            st.error(str(e))
            st.stop()

        with open('.metadata/features.lst', 'r') as file:
            features = file.read().splitlines()
        if features != list(self.descriptors.columns[1:]):
            st.error(f'Expected features do not match the given features. Please build the Pipeline again.')
            st.stop()
        
        from sklearn.metrics import roc_curve, auc
        fig, ax = pyplot.subplots()

        self.test_proba = self.pipeline.predict_proba(self.X_test)[:,1]
        fpr, tpr, _ = roc_curve(self.y_test, self.test_proba)
        ax.plot(fpr, tpr, label=f'Test set: {auc(fpr, tpr):>.3f}')

        self.train_proba = self.pipeline.predict_proba(self.X_train)[:,1]
        fpr, tpr, _ = roc_curve(self.y_train, self.train_proba)
        ax.plot(fpr, tpr, label=f'Training set: {auc(fpr, tpr):>.3f}')

        pyplot.xlabel('False Positive Rate')
        pyplot.ylabel('True Positive Rate')
        pyplot.title('Receiver Operating Characteristic')
        pyplot.legend()
        st.pyplot(fig)
    
    def upload_new_compounds(self):
        st.markdown('## Classify new compounds')
        file = st.file_uploader('Upload file *')
        show_file = st.empty()
        st.markdown('''\* File must contain the following columns:   
1 - "SMILES": SMILES structures of the compounds     
2 - "CID": compounds ID''')

        if not file:
            show_file.info("Please upload a file of type: .csv")
            st.stop()
        else:
            self.new_data = pd.read_csv(file)
            st.write(self.new_data.head())
        file.close()
        
        self.write_smiles(self.new_data, '.metadata/smiles2.smi')
        if self.calc == 'mordred':
            self.write_mordred_descriptors('.metadata/smiles2.smi', '.metadata/csv/mordred2.csv')
            # Read MORDRED descriptors
            descriptors = pd.read_csv('.metadata/csv/mordred2.csv.gz', compression='gzip')
            descriptors.rename(columns={'name':'CID'}, inplace=True)
            self.new_data = pd.merge(self.new_data, descriptors[self.descriptors.columns], on=['CID'])
        elif self.calc == 'rdkit':
            self.write_rdkit_descriptors('.metadata/smiles2.smi', '.metadata/csv/rdkit2.csv')
            # Read RDKit descriptors
            descriptors = pd.read_csv('.metadata/csv/rdkit2.csv.gz', compression='gzip')
            self.new_data = pd.merge(self.new_data, descriptors[self.descriptors.columns], on=['CID'])
        else:
            file = st.file_uploader('Upload the descriptors file for the new compounds')
            show_file = st.empty()

            if not file:
                show_file.info("Please upload a file of type: .csv")
                st.stop()
            else:
                descriptors = pd.read_csv(file)
                if not 'CID' in descriptors.columns:
                    st.error('Compounds must be identified by "CID"')
                    st.stop()
            file.close()
            try:
                self.new_data = pd.merge(self.new_data, descriptors[self.descriptors.columns], on=['CID'])
            except KeyError as e:
                st.error('''Expected features do not match the given features. 
Please make sure that the input file contains the same descriptors used for training the model.''')
                st.stop()
            
    def pipeline_predict(self):
        st.markdown('### **Predictions**')
        descriptors_list = self.descriptors.columns[1:].tolist()
        X_val = self.new_data[descriptors_list]
        st.write('Model input features: ')
        st.write(descriptors_list)

        y_pred  = self.pipeline.predict(X_val)
        y_proba = self.pipeline.predict_proba(X_val)[:,1]




        # Active ou inactive no lugar de 0 ou 1
        # Mostrar numero de ativos ou inativos

        predictions = self.new_data[['CID']].copy()
        predictions['prediction'] = y_pred
        predictions['probability'] = y_proba
        predictions.sort_values('probability', ascending=False, inplace=True)

        st.write('Top compounds:')
        st.write(predictions.head())

        predictions.to_csv('predictions.csv', index=False)
        st.write('Compounds saved to "predictions.csv".')

    @staticmethod
    def copyright_note():
        st.markdown('----------------------------------------------------')
        st.markdown('Copyright (c) 2021 CAIO C. ROCHA, DIEGO E. B. GOMES')
        st.markdown('Definir/atualizar copyright quando estiver pronto')




def main() :
    # """Run this function to display the Streamlit app"""
    # st.info(__doc__)

    # Config
    DATA_URL = ('https://covid.postera.ai/covid/activity_data.csv')
    app = App(DATA_URL)

    if app.descriptors is not None:
        app.merged_data = app.merge_dataset()
        app.feature_selection()

        st.write('# Machine learning')
        app.split_X_and_y()
        model_name, model = app.select_model()
        if st.checkbox('Build Pipeline'):
            app.mlpipeline(model_name, model)
        
        app.train_test_proba(model_name)
        app.upload_new_compounds()
        app.pipeline_predict()
        
    #mlpipeline2()

    # Copyright footnote
    app.copyright_note()

if __name__== '__main__': main()
