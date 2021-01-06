import os
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
        self.merge_data = None
        
    
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
        self.data[['SMILES','CID']].to_csv('smiles.smi',sep='\t',header=None,index=False)
        #st.write('Wrote smiles.smi')

    @staticmethod
    def write_mordred_descriptors() :
        #st.write("Cache in in run_mordred: expensive_computation")
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
                return
            else:
                descriptors = pd.read_csv(file)
                if not 'CID' in descriptors.columns:
                    st.error('Compounds must be identified by "CID"')
                    return
            file.close()
        
        st.dataframe(descriptors.head())
        # descriptors_list = descriptors.columns.tolist()[1:]
        # selected_feature = st.sidebar.selectbox(label="Descriptors",
        #                                     options=(descriptors_list))
        
        # # Plot
        # st.markdown(f"### Selection: {selected_feature}")
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

        # Put a label on it
        self.data['activity'] = 0
        self.data.loc[self.data[activity_label] > 50 , 'activity'] = 1
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

        # Create sublists
        actives   = self.data.query(f'{activity_label} > 50')
        inactives = self.data.query(f'{activity_label} <= 50')

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

        if not st.checkbox('Hide graph', False, key=1):
            fig, ax = pyplot.subplots(figsize=(15,5))
            sns.histplot(df_filtered[activity_label], kde=True, ax=ax)
            st.pyplot(fig)
        
    @st.cache(suppress_st_warning=True)
    def merge_dataset(self):
        #st.write("Cache in merge_dataset: expensive_computation")
        # Merge the dataset to include activity data and descriptors.
        merged_data = pd.merge(self.data[['CID', self.activity_label, 'activity']].dropna(), 
                            self.descriptors, on=['CID'])

        # Write Merged Dataset
        if not os.path.isfile('merged.csv') :
            merged_data.to_csv('merged.csv',index=False)

        return merged_data

    def show_merged_data(self):
        if st.checkbox('Show labeled compounds'):
            st.subheader('Merged data')
            st.write(self.merged_data)

    def feature_cross_correlation(self):
        #st.write("No cache in feature_cross_correlation")
        # Insert user-controlled values from sliders into the feature vector.
        # for feature in control_features:
        #     features[feature] = st.sidebar.slider(feature, 0, 100, 50, 5)

        X = self.merged_data.drop(['CID','activity'], axis=1).dropna(axis=1) # All but "CID" and "activity"
        Y = self.merged_data[self.activity_label]

        # Create the sidebar slider for VarianceThreshold
        value = st.sidebar.slider("Variance Threshold", 0.1, 1.0, 0.3)

        from sklearn.feature_selection import VarianceThreshold
        var = VarianceThreshold(threshold=value)
        var = var.fit(X.iloc[:,1:], Y) # All but the activity_label

        st.markdown('## Cross correlation')
        state = st.text('Computing cross correlation among descriptors...')
        cor = X.corr()
        st.subheader('Head(5)')
        st.write(cor.head(5))

        if st.checkbox('Show entire DataFrame', False, key=1):
            if len(cor) <= 100:
                st.write(cor)
            else:
                st.error("Sorry, large DataFrames can't be displayed!")

        if st.checkbox('Show correlation HeatMap', False, key=1):
            fig, ax = pyplot.subplots(figsize=(10,10))
            sns.heatmap(cor, annot=True, cmap='Reds',square=True,ax=ax)
            st.pyplot(fig)


        st.markdown('# Ignore everything bellow')
        st.markdown('# Feature selection')

        # Select the features within the threshold
        cols = var.get_support(indices=True)
        features = X.columns[cols]
        st.write(f'Features within the threshold ({value})')
        st.write(features.tolist())

        # Now filter out correlations with the Target Variable
        # Consider correlations only with the target variable
        # cor_target = abs(cor['f_inhibition_at_50_uM'])

        # Select correlations with a correlation above a threshold
        # features = cor_target[cor_target>value]
      
    def mlpipeline(self):
        st.write('# Machine learning')
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from imblearn.over_sampling import SMOTE
        from imblearn.pipeline import make_pipeline
        from sklearn.ensemble import RandomForestClassifier

        X = self.merged_data[self.descriptors.columns[1:]]
        y = self.merged_data['activity']
        st.write(len(X), len(y))

        X_aux, X_val, y_aux, y_val = train_test_split(X, y, test_size=0.2, random_state=1)
        X_train, X_test, y_train, y_test = train_test_split(X_aux, y_aux, test_size=0.2, random_state=2)
        st.write(len(X_aux), len(y_aux), len(X_val), len(y_val), len(X_train), len(y_train), len(X_test), len(y_test))

        model = RandomForestClassifier(n_estimators=40, max_depth=6, random_state=13)
        pipe = make_pipeline(SMOTE(random_state=42), StandardScaler(), model)
        model_fitted = pipe.fit(X_train, y_train)

        from sklearn.metrics import roc_curve, auc
        fig, ax = pyplot.subplots()

        y_pred_train = model_fitted.predict(X_train)
        fpr, tpr, _ = roc_curve(y_train, y_pred_train)
        ax.plot(fpr, tpr, label=f'Train set: {auc(fpr, tpr):>.3f}')

        y_pred = model_fitted.predict(X_test)
        fpr, tpr, _ = roc_curve(y_test, y_pred)
        ax.plot(fpr, tpr, label=f'Test set: {auc(fpr, tpr):>.3f}')

        y_pred_val = model_fitted.predict(X_val)
        fpr, tpr, _ = roc_curve(y_val, y_pred_val)
        ax.plot(fpr, tpr, label=f'Validation set: {auc(fpr, tpr):>.3f}')

        pyplot.legend()
        st.pyplot(fig)

    @staticmethod
    def copyright_note():
        st.markdown('Copyright (c) 2021 DIEGO E. B. GOMES, CAIO C. ROCHA')
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
        app.mlpipeline()
    #mlpipeline2()

    # Copyright footnote
    app.copyright_note()

if __name__== '__main__': main()
