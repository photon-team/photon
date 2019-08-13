from photonai.base.PhotonBase import Hyperpipe, PipelineElement, OutputSettings, PreprocessingPipe
from photonai.optimization.Hyperparameters import Categorical
from photonai.neuro.NeuroBase import NeuroModuleBranch

from sklearn.model_selection import ShuffleSplit
from nilearn.datasets import fetch_oasis_vbm

import time
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


# GET DATA FROM OASIS
n_subjects = 50
dataset_files = fetch_oasis_vbm(n_subjects=n_subjects)
age = dataset_files.ext_vars['age'].astype(float)
y = np.array(age)
X = np.array(dataset_files.gray_matter_maps)


# DESIGN YOUR PIPELINE
settings = OutputSettings(project_folder='.')

my_pipe = Hyperpipe('Limbic_Pipeline',
                    optimizer='grid_search',
                    metrics=['mean_absolute_error'],
                    best_config_metric='mean_absolute_error',
                    outer_cv=ShuffleSplit(n_splits=2, test_size=0.2),
                    inner_cv=ShuffleSplit(n_splits=2, test_size=0.2),
                    verbosity=1,
                    cache_folder="./cache",
                    output_settings=settings)

# CREATE NEURO BRANCH
# specify the number of processes that should be used
neuro_branch = NeuroModuleBranch('NeuroBranch', nr_of_processes=1)

# resample images to a desired voxel size - this also works with voxel_size as hyperparameter
# it's also very reasonable to define a batch size for a large number of subjects
neuro_branch += PipelineElement('ResampleImages', hyperparameters={'voxel_size': Categorical([3, 5])}, batch_size=20)

# additionally, you can smooth the entire image
neuro_branch += PipelineElement('SmoothImages', {'fwhm': Categorical([6, 8])}, batch_size=20)

# now, apply a brain atlas and extract 4 ROIs
# set "extract_mode" to "vec" so that all voxels within these ROIs are vectorized and concatenated
neuro_branch += PipelineElement('BrainAtlas', hyperparameters={},
                                rois=['Hippocampus_L', 'Hippocampus_R', 'Amygdala_L', 'Amygdala_R'],
                                atlas_name="AAL", extract_mode='vec', batch_size=20)

# finally, add your neuro branch to your hyperpipe
my_pipe += neuro_branch

# now, add standard ML algorithms to your liking
my_pipe += PipelineElement('StandardScaler')

my_pipe += PipelineElement('SVR', hyperparameters={'kernel': Categorical(['rbf', 'linear'])}, gamma='scale')

# NOW TRAIN YOUR PIPELINE
start_time = time.time()
my_pipe.fit(X, y)
elapsed_time = time.time() - start_time
print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))

debug = True

