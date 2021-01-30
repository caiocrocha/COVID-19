# Usar postera inteiro como conjunto de treinamento (opcao, elimina teste)
# Upload dados de treinamento, teste (generalizacao)

# Colocar opcao de usar descritores otimos (se selecionado rdkit) de acordo com o classificador
# Otimizar: calculo dos descritores para os novos dados (new_data)

# Opcoes: baixar resultados e baixar modelo pickle
# Colocar SelectKBest com escolha de K

# Escrever requirements, adicionar mordred e rdkit

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

        ########################
        # Load Activity data 
        ########################
        st.markdown('## **Activity data**')
        st.markdown('### Visualizing properties')
        self.data = self.download_activity(DATA_URL)
        self.write_smiles(self.data, 'smiles.smi')

        #######################
        # Summary of the data 
        #######################
        self.activity_label = None
        self.show_properties() # show properties and set activity label

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
        st.sidebar.image('Logo_medium.png')

    @staticmethod
    def show_description():
        st.markdown('''## **Welcome to**
# SARS-CoV-2
## Machine Learning Drug Hunter
A straightforward tool that combines experimental activity data, molecular descriptors and machine learning 
for classifying potential drug candidates against SARS-CoV-2 Main Protease (MPro).     
We use the **COVID Moonshot**, a public collaborative initiatiave by **PostEra**, as the dataset of compounds containing 
the experimental activity data for the machine learning classifiers. The molecular descriptors can 
be automatically calculated with Mordred or RDKit, or you can also provide a CSV file of molecular descriptors 
calculated with an external program of your preference.     
<sub>We'd like to send our deepest thanks to **PostEra**, without which this work wouldn't have been possible. </sub>
''', unsafe_allow_html=True)

    @st.cache(suppress_st_warning=True, allow_output_mutation=True)
    def download_activity(self, DATA_URL) :
        # Verbose
        st.text('Fetching data from PostEra... ')
        data_load_state = st.markdown('Loading activity data...')
        if os.path.isfile('csv/activity.csv') :
            data = pd.read_csv('csv/activity.csv')
        else :
            data = pd.read_csv(DATA_URL)
            data.to_csv('csv/activity.csv', index=False)
        data_load_state.text('Done! (using cache)')
        st.text('Data saved to "csv/activity.csv"')
        return data
    
    @staticmethod
    @st.cache(suppress_st_warning=True, allow_output_mutation=True)
    def write_smiles(data, smiles):
        # Write smiles to disk
        data[['SMILES','CID']].to_csv(smiles, sep='\t', header=None, index=False)

    @staticmethod
    @st.cache(suppress_st_warning=True)
    def write_mordred_descriptors(smiles, csv) :
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
            lista = [calculator.CalcDescriptors(m) for m in mols]
            
            descriptors = pd.DataFrame(lista, columns=descriptors_list)
            descriptors.insert(0, column='CID', value=self.data['CID'])
            descriptors.to_csv(f'{csv}.gz', index=False, compression='gzip')

    def calculate_descriptors(self):
        st.markdown("## **Descriptors**")
        if st.checkbox('Calculate Mordred descriptors'):
            self.write_mordred_descriptors('smiles.smi', 'csv/mordred.csv')
            # Read MORDRED descriptors
            descriptors = pd.read_csv('csv/mordred.csv.gz', compression='gzip')
            descriptors.rename(columns={'name':'CID'}, inplace=True)
            self.calc = 'mordred' # control variable
        elif st.checkbox('Calculate RDKit descriptors'):
            self.write_rdkit_descriptors('smiles.smi', 'csv/rdkit.csv')
            # Read RDKit descriptors
            descriptors = pd.read_csv('csv/rdkit.csv.gz', compression='gzip')
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
            [f'Select all ({len(descriptors_list)})'] + descriptors_list))
        if 'Select all' in selected:
            selected = descriptors_list
        st.write("You selected", len(selected), "features")

        if not selected:
            st.stop()
        
        descriptors = descriptors[['CID'] + selected]
        return descriptors
        
    def show_properties(self):
        # List numeric columns
        numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
        data_numeric = self.data.select_dtypes(include=numerics).columns.tolist()
        #data_numeric=data_numeric.to_numeric()
        if 'activity' in data_numeric:
            data_numeric.remove('activity')

        ########################
        # Explore data
        ########################

        # Create a sidebar dropdown to select property to show.
        activity_label = st.sidebar.selectbox(label="Properties *",
                                        options=([None, *data_numeric]))
        st.sidebar.markdown('''<sub>* The classifier will be trained accordingly to the selected property. 
If no property is selected, then "f_inhibition_at_50_uM" will be used for labeling the compounds.    
A compound will be considered to be active if `Property > 50`. This value can be adjusted with the slider below.</sub>''', 
unsafe_allow_html=True)
        
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

        # Put a label on it
        threshold = st.sidebar.slider("Threshold for selecting active compounds:", 0, 100, value=50)
        self.data['activity'] = 0
        self.data.loc[self.data[activity_label] > threshold, 'activity'] = 1

        # Create sublists
        actives   = self.data.query(f'{activity_label} > {threshold}')
        inactives = self.data.query(f'{activity_label} <= {threshold}')

        st.text('')
        st.markdown(f'''
        |Compounds|Active|Inactive|
        |---|---|---|
        |{len(self.data)}|{len(actives)}|{len(inactives)}|
        ''')

        st.text('')
        if st.checkbox('Show raw data'):
            st.subheader('Raw data')
            st.write(self.data)

        if st.checkbox('Show filtered compounds'):
            st.subheader('Filtered compounds')
            st.write(df_filtered)

        if not st.checkbox('Hide graph'):
            fig, ax = pyplot.subplots(figsize=(15,5))
            sns.histplot(df_filtered[activity_label], kde=True, ax=ax)
            st.pyplot(fig)
        
    def merge_dataset(self):
        # Merge the dataset to include activity data and descriptors.
        merged_data = pd.merge(self.data[['CID', self.activity_label, 'activity']].dropna(), 
                            self.descriptors, on=['CID'])
        # Write Merged Dataset
        if not os.path.isfile('csv/merged.csv'):
            merged_data.to_csv('csv/merged.csv', index=False)

        return merged_data

    def show_merged_data(self):
        if st.checkbox('Show labeled compounds'):
            st.subheader('Merged data')
            st.write(self.merged_data.head())

    def feature_cross_correlation(self):
        # Insert user-controlled values from sliders into the feature vector.
        # for feature in control_features:
        #     features[feature] = st.sidebar.slider(feature, 0, 100, 50, 5)
        st.markdown('# Feature selection')
        st.markdown('''Filter the selected descriptors. \*    
<sub> \* The steps bellow are applied sequentially.</sub>''', unsafe_allow_html=True)

        st.markdown('## Cross Correlation')
        if st.checkbox('Compute cross correlation between features', True):
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
                fig, ax = pyplot.subplots(figsize=(10,10))
                sns.heatmap(corr, annot=True, cmap='Reds', square=True, ax=ax)
                st.pyplot(fig)

            # Consertar (remover entre elas, não somente correlacionado à atividade)
            if st.checkbox('Remove highly correlated features (|Correlation| > Correlation Threshold)', True):
                value = st.slider("Correlation Threshold", 0.0, 1.0, value=0.95)

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

        st.markdown('## Variance Thresholding')
        # Create the sidebar slider for VarianceThreshold
        value = st.slider("Variance Threshold", 0.0, 1.0, value=0.3)
        if st.checkbox('Filter out features with variance bellow the threshold'):
            from sklearn.feature_selection import VarianceThreshold

            X = self.merged_data.drop(['CID','activity', self.activity_label], axis=1).dropna(axis=1)
            Y = self.merged_data[self.activity_label]
            var = VarianceThreshold(threshold=value)
            var = var.fit(X, Y)

            # Get features within the threshold
            cols = var.get_support(indices=True)
            features = X.columns[cols].tolist()

            # Remove features NOT within the threshold
            to_drop = X.columns[~X.columns.isin(features)].tolist()
            st.write('Removed features: ')
            st.write(to_drop)
            
            self.descriptors.drop(to_drop, axis=1, inplace=True)
            self.merged_data.drop(to_drop, axis=1, inplace=True) 

        if st.checkbox('Show filtered data'):
            st.write(self.merged_data.head())
            
    @staticmethod
    def select_model():
        model_list = ['RandomForestClassifier', 'XGBClassifier', 'KNeighborsClassifier']
        model_name = st.sidebar.selectbox(label="Classifier", options=(model_list))

        st.sidebar.markdown('''<sub>Note: The hyperparaters showed bellow are the optimal parameters found in our study. 
Nevertheless, feel free to change them as you will.</sub>''', unsafe_allow_html=True)
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
        with open('features.lst', 'w+') as features_file:
            features_file.write("\n".join(features))
    
    def train_test_proba(self, model_name):
        import pickle
        try:
            file = open(f'pickle/{model_name}.pickle', 'rb')
            self.pipeline = pickle.load(file)
            file.close()
        except OSError as e:
            st.error("Oops! It seems the model hasn't been trained yet")
            st.error(str(e))
            st.stop()

        with open('features.lst', 'r') as file:
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
        ax.plot(fpr, tpr, label=f'Train set: {auc(fpr, tpr):>.3f}')

        pyplot.xlabel('False Positive Rate')
        pyplot.ylabel('True Positive Rate')
        pyplot.title('Receiver Operating Characteristic')
        pyplot.legend()
        st.pyplot(fig)
    
    def upload_new_compounds(self):
        st.markdown('## Classify new compounds')
        file = st.file_uploader('Upload file *')
        show_file = st.empty()
        st.markdown('''<sub> \* File must contain the following columns:   
1 - "SMILES": SMILES structures of the compounds     
2 - "CID": compounds ID</sub>''', unsafe_allow_html=True)

        if not file:
            show_file.info("Please upload a file of type: .csv")
            st.stop()
        else:
            self.new_data = pd.read_csv(file)
            st.write(self.new_data.head())
        file.close()
        
        self.write_smiles(self.new_data, 'smiles2.smi')
        if self.calc == 'mordred':
            self.write_mordred_descriptors('smiles2.smi', 'csv/mordred2.csv')
            # Read MORDRED descriptors
            descriptors = pd.read_csv('csv/mordred2.csv.gz', compression='gzip')
            descriptors.rename(columns={'name':'CID'}, inplace=True)
            self.new_data = pd.merge(self.new_data, descriptors[self.descriptors.columns], on=['CID'])
        elif self.calc == 'rdkit':
            self.write_rdkit_descriptors('smiles2.smi', 'csv/rdkit2.csv')
            # Read RDKit descriptors
            descriptors = pd.read_csv('csv/rdkit2.csv.gz', compression='gzip')
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

        predictions = self.new_data[['CID']].copy()
        predictions['prediction'] = y_pred
        predictions['probability'] = y_proba
        predictions.sort_values('probability', ascending=False, inplace=True)

        st.write('Top compounds:')
        st.write(predictions.head())

        predictions.to_csv('csv/predictions.csv', index=False)
        st.write('Compounds saved to "csv/predictions.csv".')

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
        app.show_merged_data()
        app.feature_cross_correlation()

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
