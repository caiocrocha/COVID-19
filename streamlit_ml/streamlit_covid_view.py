import os
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib import pyplot

# Config
DATA_URL = ('https://covid.postera.ai/covid/activity_data.csv')

# Functions
@st.cache(suppress_st_warning=True)
def download_activity() :
    if os.path.isfile('activity.csv') :
        data = pd.read_csv('activity.csv')
    else :
        data = pd.read_csv(DATA_URL)
    data.to_csv('activity.csv',index=False)
    return data

@st.cache(suppress_st_warning=True)
def run_mordred() :
    '''
    Could not make mordred work with rdkit.
        There is a lot of (unsolved) confusion with library compatibility
    '''
    # Let's rely on the Stupid way
    if os.path.isfile('smiles.smi') and not os.path.isfile('descriptors.csv.gz'):
        os.system('python -m mordred smiles.smi > descriptors.csv')

    if os.path.isfile('descriptors.csv'):
        os.system('gzip descriptors.csv')

@st.cache(suppress_st_warning=True) 
def mlpipeline() :
  # H2O 
  # Load the H2O library and start up the H2O cluter locally on your machine
  import h2o

  # Number of threads, nthreads = -1, means use all cores on your machine
  # max_mem_size is the maximum memory (in GB) to allocate to H2O
  h2o.init(nthreads = -1, max_mem_size = 8)

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

  y = 'kind'
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



# Program


########################
# Load Activity data 
########################
# Verbose
data_load_state = st.markdown('Loading activity data...')
data = download_activity()
data_load_state.text("Done! (using st.cache)")


# List numeric columns
numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
data_numeric = data.select_dtypes(include=numerics).columns.tolist()
#data_numeric=data_numeric.to_numeric()

# Create sublists
actives=data.query('f_inhibition_at_50_uM >= 50')
inactives=data.query('f_inhibition_at_50_uM < 50')

# Put a label on it
data['kind']=0
data.loc[ data['r_inhibition_at_50_uM'] >= 50 , 'kind'] = 1


# Write smiles to disk
data[['SMILES','CID']].to_csv('smiles.smi',sep='\t',header=None,index=False)
st.write('Wrote smiles.smi')

# Run MORDRED with smiles file.
run_mordred()

# Read MORDRED descriptors
descriptors = pd.read_csv('descriptors.csv.gz',compression='gzip')

# Summary:
st.markdown(f'''
|Compounds|Active|Inactive|
|---|---|---|
|{len(data)}|{len(actives)}|{len(inactives)}|

''')


########################
# Explore data
########################

# Create a sidebar dropdown to select property to show.
pick_properties = st.sidebar.selectbox(label="Properties",
                                  options=(data_numeric))

# Create a sidebar slider to filter property
## Step 1 - Pick min & max for picked property 
max_val=float(data[pick_properties].max())
min_val=float(data[pick_properties].min())
mean_val=float(data[pick_properties].mean())


## Step 2 - Create the sidebar slider
min_filter,max_filter = st.sidebar.slider("Filter by: "+pick_properties, 
                           min_val,
                           max_val,
                           (min_val, max_val))

df_properties = data[['CID',pick_properties]].dropna()
df_filtered = df_properties[df_properties[pick_properties].between(float(min_filter),float(max_filter))]

st.markdown(f'''
| Property | Min | Max | Mean |
| --- | --- | --- | --- |
| {pick_properties} | {min_val:2g} | {max_val:2g} | {mean_val:2g} |

''')

if st.checkbox('Show filtered data'):
    st.subheader('Filtered data')
    st.write(df_filtered)


# Insert user-controlled values from sliders into the feature vector.
#for feature in control_features:
#    features[feature] = st.sidebar.slider(feature, 0, 100, 50, 5)


data_tidy=data.melt(id_vars='CID')

selected_features = st.sidebar.selectbox(label="Descriptors",
                                         options=(descriptors.columns.tolist()))
# Plot
st.markdown("## **Descriptor**")
st.markdown(f"### Selection: {selected_features}")

if not st.checkbox('Hide Graph', False, key=1):
    fig, ax = pyplot.subplots(figsize=(15,5))
    sns.histplot(df_properties[pick_properties],kde=True,ax=ax)
    st.pyplot(fig)




###########################
# Machine Learning features
###########################
# Merge the dataset to include activity data and descriptors.
dataset = pd.merge(data[['CID','f_inhibition_at_50_uM','kind']].dropna(),descriptors.rename(columns={'name':'CID'}))


# Write Merged Dataset
if not os.path.isfile('merged.csv') :
    dataset.to_csv('merged.csv',index=False)


# 
if st.checkbox('Show merged data'):
    st.subheader('Merged data')
    st.write(dataset.head(10))


# 
X = dataset.iloc[:, 2:] # All but "CID" and "f_inhibition_at_50_uM"
X = X.dropna(axis=1)
Y = dataset[['f_inhibition_at_50_uM']]

###########################
# Feature cross correlation
############################
# Create the sidebar slider for VarianceThreshold
Variance_Threshold = st.sidebar.slider("Variance Threshold [0.3]",0.1,1.0,0.3)

from sklearn.feature_selection import VarianceThreshold
var = VarianceThreshold(threshold=0.3)
var = var.fit(X,Y)

st.write('computing cross correlation among descriptors')
cor = X.corr()

st.write('Cross correlation [head(5)]')
st.write(cor.head())

if st.checkbox('Show correlation HeatMap',False, key=1):
    fig, ax = pyplot.subplots(figsize=(10,10))
    sns.heatmap(cor, annot=False, cmap='Reds',square=True,ax=ax)
    st.pyplot(fig)



# Launch the ML pipeline
mlpipeline()

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











st.markdown('# Ignore everything bellow')





# Select the features within the Threshold
cols = var.get_support(indices=True)
features = X.columns[cols]
st.write('Features within the Threshold')
st.write(features.tolist())


# Now filter out correlations with the Target Variable
# Consider correlations only with the target variable
cor_target = abs(cor['f_inhibition_at_50_uM'])

#Select correlations with a correlation above a threshold
features = cor_target[cor_target>0.1]


########################
# Show Raw data
########################
if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)

if st.checkbox('Show tidy data'):
    st.subheader('Tidy data')
    st.write(data_tidy)

def main() :
    """Run this function to display the Streamlit app"""

    st.info(__doc__)

    file = st.file_uploader("Upload file")

    show_file = st.empty()

    if not file:
        show_file.info("Please upload a file of type: .csv")
        return
    else:
        data = pd.read_csv(file)
        st.dataframe(data.head(10))

    file.close()

#main()
download_activity() 
