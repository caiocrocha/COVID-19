# Escrever requirements
# Colocar SelectKBest com escolha de K
# Corrigir slider "properties"
# Calcular descritores com rdkit

# Upload de arquivo com descritores -> rotula atividade -> classifica compostos

import os
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib import pyplot

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
        self.data = self.download_activity(DATA_URL)
        self.write_smiles()

        #######################
        # Summary of the data 
        #######################
        self.activity_label = None
        self.show_properties()

        #######################
        # Load descriptors 
        #######################
        self.descriptors = self.calculate_descriptors()
        self.merged_data = None
        
        #######################
        # ML 
        #######################
        self.pipeline = None
    
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
        if os.path.isfile('activity.csv') :
            data = pd.read_csv('activity.csv')
        else :
            data = pd.read_csv(DATA_URL)
            data.to_csv('activity.csv', index=False)
        data_load_state.text('Done! (using cache)')
        st.text('Data saved to "activity.csv"')
        return data
    
    @st.cache(suppress_st_warning=True, allow_output_mutation=True)
    def write_smiles(self):
        # Write smiles to disk
        self.data[['SMILES','CID']].to_csv('smiles.smi', sep='\t', header=None, index=False)
        #st.write('Wrote smiles.smi')

    @staticmethod
    @st.cache(suppress_st_warning=True)
    def write_mordred_descriptors() :
        st.write("Cache in in run_mordred: expensive_computation")
        # Run MORDRED with smiles file.
        '''
        Could not make mordred work with rdkit.
            There is a lot of (unsolved) confusion with library compatibility
        '''
        # Let's rely on the manual way
        if os.path.isfile('smiles.smi') and not os.path.isfile('descriptors.csv.gz'):
            os.system('python -m mordred smiles.smi > descriptors.csv')

        if os.path.isfile('descriptors.csv'):
            os.system('gzip descriptors.csv')

    def calculate_descriptors(self):
        st.markdown("## **Descriptors**")
        if st.checkbox('Calculate Mordred descriptors'):
            self.write_mordred_descriptors()
            # Read MORDRED descriptors
            descriptors = pd.read_csv('descriptors.csv.gz', compression='gzip')
            descriptors.rename(columns={'name':'CID'}, inplace=True)
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
        
        st.dataframe(descriptors.head())

        descriptors_list = descriptors.columns.tolist()[1:]
        selected = st.multiselect(label="Select descriptors", options=(descriptors_list))
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
        activity_label = st.sidebar.selectbox(label="Properties",
                                        options=([None, *data_numeric]))
        
        if activity_label is None:
            activity_label = 'f_inhibition_at_50_uM'

        self.activity_label = activity_label

        # Create a sidebar slider to filter property
        ## Step 1 - Pick min & max for picked property 
        max_val  = float(self.data[activity_label].max())
        min_val  = float(self.data[activity_label].min())
        #mean_val = float(self.data[activity_label].mean())

        ## Step 2 - Create the sidebar slider
        min_filter, max_filter = st.sidebar.slider("Filter by: " + activity_label, 
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
        threshold = st.sidebar.slider(f"Threshold for selecting active compounds: \n(Activity > Threshold)", 0, 100, value=50)
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
        
    @st.cache(suppress_st_warning=True, allow_output_mutation=True)
    def merge_dataset(self):
        # Merge the dataset to include activity data and descriptors.
        merged_data = pd.merge(self.data[['CID', self.activity_label, 'activity']].dropna(), 
                            self.descriptors, on=['CID'])

        # Write Merged Dataset
        if not os.path.isfile('merged.csv'):
            merged_data.to_csv('merged.csv', index=False)

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
        X = self.merged_data.drop(['CID','activity'], axis=1).dropna(axis=1) # All but "CID" and "activity"
        Y = self.merged_data[self.activity_label]

        if st.checkbox('Cross Correlation', True):
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

        if st.checkbox('Variance Thresholding'):
            # Create the sidebar slider for VarianceThreshold
            value = st.slider("Variance Threshold", 0.1, 1.0, value=0.3)

            from sklearn.feature_selection import VarianceThreshold
            var = VarianceThreshold(threshold=value)
            var = var.fit(X.iloc[:,1:], Y) # All but the activity_label

            # Select the features within the threshold
            cols = var.get_support(indices=True)
            features = X.columns[cols].tolist()
            st.write(f'Features within the threshold ({value})')
            st.write(features)
            self.descriptors = self.descriptors[['CID'] + features]
            self.merged_data = self.merged_data[['CID', self.activity_label, 'activity'] + features]

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
            return RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=13)

        elif model_name == 'XGBClassifier':
            from xgboost import XGBClassifier

            n_estimators = st.sidebar.slider("Number of Estimators", 0, 1000, value=200)
            max_depth = st.sidebar.slider("Maximum Depth per Tree", 0, 10, value=3)
            eta = st.sidebar.slider("Learning Rate (ETA)", 0.0, 1.0, value=0.1)
            return XGBClassifier(objective='reg:logistic', n_estimators=n_estimators, 
                max_depth=max_depth, eta=eta, random_state=13)

        else:
            from sklearn.neighbors import KNeighborsClassifier

            n_neighbors = st.sidebar.slider("Number of Neighbors", 0, 10, value=5)
            return KNeighborsClassifier(n_neighbors=n_neighbors)

    # Train com cache não funciona
    #@st.cache(suppress_st_warning=True)
    def mlpipeline(self, model):
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from imblearn.over_sampling import SMOTE
        from imblearn.pipeline import Pipeline

        X = self.merged_data[self.descriptors.columns[1:]]
        y = self.merged_data['activity']
        st.write(len(X), len(y))

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=27)
        st.write(len(X_train), len(y_train), len(X_test), len(y_test))

        self.pipeline = Pipeline(steps=[('smote', SMOTE(random_state=42)), 
                                        ('scaler', StandardScaler()), 
                                        ('clf', model)
                                        ])
        self.pipeline.fit(X_train, y_train)

        model_name = str(self.pipeline['clf']).split('(')[0]

        import pickle
        # Serialize model
        if not os.path.isdir('pickle'):
            os.mkdir('pickle')
        with open(f'pickle/{model_name}.pickle', 'wb') as file:
            pickle.dump(self.pipeline, file)

        from sklearn.metrics import roc_curve, auc
        fig, ax = pyplot.subplots()

        y_proba = self.pipeline.predict_proba(X_test)
        fpr, tpr, _ = roc_curve(y_test, y_proba[:,1])
        ax.plot(fpr, tpr, label=f'Test set: {auc(fpr, tpr):>.3f}')

        y_proba_train = self.pipeline.predict_proba(X_train)
        fpr, tpr, _ = roc_curve(y_train, y_proba_train[:,1])
        ax.plot(fpr, tpr, label=f'Train set: {auc(fpr, tpr):>.3f}')

        pyplot.legend()
        pyplot.savefig('roc_curve.png')
        st.pyplot(fig)

    @staticmethod
    def show_roc_curve():
        st.image('roc_curve.png')
    
    @staticmethod
    def upload_new_compounds():
        st.markdown('## Classify new compounds')
        file = st.file_uploader('Upload file')
        show_file = st.empty()

        if not file:
            show_file.info("Please upload a file of type: .csv")
            return
        else:
            new_data = pd.read_csv(file)
            st.write(new_data.head())
        file.close()
        return new_data

    def pipeline_predict(self, new_data):
        descriptors_list = self.descriptors.columns[1:].tolist()
        X_val = new_data[descriptors_list]
        y_val = new_data['f_activity']
        st.write('Model input features: ')
        st.write(descriptors_list)

        y_proba = self.pipeline.predict_proba(X_val)

        from sklearn.metrics import roc_curve, auc
        fig, ax = pyplot.subplots()
        fpr, tpr, _ = roc_curve(y_val, y_proba[:,1])
        ax.plot(fpr, tpr, label=f'Validation set: {auc(fpr, tpr):>.3f}')
        ax.legend()
        st.pyplot(fig)

    @staticmethod
    def copyright_note():
        st.markdown('----------------------------------------------------')
        st.markdown('Copyright (c) 2021 CAIO C. ROCHA, DIEGO E. B. GOMES')
        st.markdown('Definir/atualizar copyright quando estiver pronto')



@st.cache(suppress_st_warning=True)
def mlpipeline2() :
    ###########################
    # Machine Learning features
    ###########################
    # H2O 
    # Load the H2O library and start up the H2O cluster locally on your machine
    import h2o

    # Number of threads, nthreads = -1, means use all cores on your machine
    # max_mem_size is the maximum memory (in GB) to allocate to H2O
    nproc = os.cpu_count()
    h2o.init(nthreads = nproc-1, max_mem_size = 8)

    h2o_data = h2o.import_file('merged.csv',header=1)

    # Partition data into 70%, 15%, 15% chunks
    # Setting a seed will guarantee reproducibility
    splits = h2o_data.split_frame(ratios=[0.7, 0.15], seed=1)
    train = splits[0]
    valid = splits[1]
    test = splits[2]

    st.markdown(f'''
    | Set | Instances |
    | --- | --- |
    | Train | {train.nrow} |
    | Validation | {valid.nrow}|
    | Test | {test.nrow}|
    ''')

    y = 'activity'
    x = list(h2o_data.columns)
    x.remove(y)  #remove the response variable
    x.remove('CID')  #remove the interest rate column because it's correlated with the outcome


    # Import H2O GBM:
    from h2o.estimators.gbm import H2OGradientBoostingEstimator

    # Initialize and train the GBM estimator:
    st.write('[GBM 1] Initializing the GBM estimator')
    gbm_fit1 = H2OGradientBoostingEstimator(model_id='gbm_fit1', seed=1)

    st.write('[GBM 1] Training the GBM estimator... please wait')
    gbm_fit1.train(x=x, y=y, training_frame=train)


    # Train a GBM with more trees
    #  st.write('[GBM 2] Initializing the GBM estimator with 500 trees' )
    #  gbm_fit2 = H2OGradientBoostingEstimator(model_id='gbm_fit2', ntrees=500, seed=1)

    #  st.write('[GBM 2] Training the GBM estimator... please wait (GBM2)')
    #  gbm_fit2.train(x=x, y=y, training_frame=train)

    #  st.write('[GBM 3] Initializing the GBM estimator with 500 trees and early stop')
    ## Now let's use early stopping to find optimal ntrees
    #  gbm_fit3 = H2OGradientBoostingEstimator(model_id='gbm_fit3', 
    #                                        ntrees=500, 
    #                                        score_tree_interval=5,     #used for early stopping
    #                                        stopping_rounds=3,         #used for early stopping
    #                                        stopping_metric='AUC',     #used for early stopping
    #                                        stopping_tolerance=0.0005, #used for early stopping
    #                                        seed=1)

    #  st.write('[GBM 3] Training the GBM estimator... please wait (GBM3)')
    # The use of a validation_frame is recommended with using early stopping
    #  gbm_fit3.train(x=x, y=y, training_frame=train, validation_frame=valid)

    # Evaluate the model performance
    gbm_perf1 = gbm_fit1.model_performance(test)
    #gbm_perf2 = gbm_fit2.model_performance(test)
    #gbm_perf3 = gbm_fit3.model_performance(test)


    # Retreive test set AUC
    st.markdown(f'''
    | Model | AUC | 
    | ----- | --- |
    | GBM1  | {gbm_perf1.auc()} |
    ''')
    #| GBM2  | {gbm_perf2.auc()} |
    #''')
    #| GBM3  | {gbm_perf3.auc()} | 
    #''')

def main() :
    # """Run this function to display the Streamlit app"""
    # st.info(__doc__)

    # file = st.file_uploader("Upload file")

    # show_file = st.empty()

    # if not file:
    #     show_file.info("Please upload a file of type: .csv")
    #     return
    # else:
    #     data = pd.read_csv(file)
    #     st.dataframe(data.head())

    # file.close()

    # Config
    DATA_URL = ('https://covid.postera.ai/covid/activity_data.csv')
    app = App(DATA_URL)

    if app.descriptors is not None:
        app.merged_data = app.merge_dataset()
        app.show_merged_data()
        app.feature_cross_correlation()

        # Launch the ML pipeline
        st.write('# Machine learning')
        model = app.select_model()
        if st.checkbox('Train the ML model'):
            app.mlpipeline(model)
        else:
            app.show_roc_curve()
        
        new_data = app.upload_new_compounds()
        app.pipeline_predict(new_data)
        #if st.checkbox('Predict new compounds'):
        #    app.pipeline_predict()
        
    #mlpipeline2()

    # Copyright footnote
    app.copyright_note()

if __name__== '__main__': main()
