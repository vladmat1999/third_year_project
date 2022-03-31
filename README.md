# User authetication and identification using swipe gestures

Third year project for the [University of Manchester](https://www.manchester.ac.uk/).

You can find the full project and sources for the data on the [GitHub page](https://github.com/vladmat1999/third_year_project).

## Description
The project is aimed at authenticating users using swipe gestures on mobile devices. Multiple approaches are proposed,
including an approach based on automatic feature extraction using convolutional neural networks (CNNs). Further information
can be found in the project report.

## Requirements
To run the code, Python is required (tested on Python 3.9).6. It is strongly recommended to use a virtual environment
to install the packages. After this is done, the packages from the `requirements.txt` file can be installed using
```sh
pip install -r requirements.txt
```

No special hardware is required, although a GPU is recommended. 
## Datasets
The datasets for the experiment can be downloaded [here](https://drive.google.com/drive/folders/1-5x9z2kaM1Nd--9_ZyISa3VFTrhOs6Uk?usp=sharing). These are in the form of `.pkl` files, and some
amount of parsing has been made on them in order to make loading the data faster. You can find the full, unparsed 
datasets at the following links:

* [Touchalytics dataset](http://www.mariofrank.net/touchalytics/)
* [BrainRun dataset](https://zenodo.org/record/2598135#.YkTeJy3MKUk)

Place the `datasets` folder in the root directory, or change the path in the `config.py` file.

## Running the code
Instructions on how to run the experiments can be found in the notebook files. Some experiments may require
modifying the parameters in the files, or uncommenting some lines of code. 

### user_authentication_using_engineered_features.ipynb
This notebook contains experiments regarding a 1-class SVM model for user authentication using
manually engineered features. The experiment output is a list of files, one for each
user, containing two arrays with the labels and probabilities of each swipe being an intruder or a user. These can then be used to calculate the EER.

The experiments may take a while to run, depending on the amount of data used. 

To run the experiments, set the `DATASET` variable to the desired dataset, along with the `N_THREADS` variable 
to specify the number of threads, and `OUTPUT_DIR` for the output directory.

### user_identification_model_1.ipynb
This notebook contains the experiments for the first model for user identification. Hyperparameter tuning has 
been commented out, and only the final model is presented. The experiment outputs validation and test accuracy,
as well as top 5 accuracy for each user.

### user_identification_model_2.ipynb
This notebook contains the experiments for the second model for user identification. Hyperparameter tuning has been 
left out as before, and the same results are presented. 
### user_authentication_using_model_1_features.ipynb

This notebook contains the experiments for user authentication using the 1-class SVM model, but it uses the 
first CNN model to predict the features for the swipes. The experiment is similar to the first one 
(`user_authentication_using_engineered_features`), with the only addition of requiring a `models` folder to run.

The pretrained models can be found [here](https://drive.google.com/drive/folders/1-5x9z2kaM1Nd--9_ZyISa3VFTrhOs6Uk?usp=sharing). To run it, place the `models` folder in the root directory, or change 
the parameter `MODELS_DIR` in the notebook.

The experiment runs for 10 iterations, using a different subset of users for each model (the ones that were not used for training).

### user_authentication_using_model_2_features.ipynb

Similar to the previous one, this notebook contains the experiments for user authentication using the 1-class SVM model, 
but it parses the gesture points by turning them into images and using the second CNN model to predict the features 
for the swipes. This experiment also requries a `models` folder in order to run. 

The pretrained models can be found [here](https://drive.google.com/drive/folders/1-5x9z2kaM1Nd--9_ZyISa3VFTrhOs6Uk?usp=sharing). To run it, place the `models` folder in the root directory, or change 
the parameter `MODELS_DIR` in the notebook.

The experiment runs for 10 iterations, using a different subset of users for each model (the ones that were not used for training).

### user_authentication_using_model_2_features.ipynb

WIP: aims to identify the ability of the model to reject windows of gestures infused with intruder data
### user_authentication_model_1_with_intruders.ipynb
WIP: aims to identify the ability of the model to reject windows of gestures infused with intruder data

### utlities.ipynb
This notebook contains some utility functions that are used for reading the results, calculating EER and
analyzing the effect of intruder on the 1-class SVM.