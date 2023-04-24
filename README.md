![Dashify_logo](https://user-images.githubusercontent.com/47029859/148430962-3544d715-7ace-4565-ad4d-332f7912f97a.png)


# DashifyML

A lightweight tool to manage and track your large scale machine leaning experiments. DashifyML contains two individual components, namely a multiprocessing capable logging component and a web-based visualization component.

Please note, that DashifyML is currently under heavy development, such that interfaces are still likely to change in the future. Nevertheless, every change will be noted in each version's change log. 

## Status

Build status: [![CircleCI](https://circleci.com/gh/dashifyML/dashifyML/tree/master.svg?style=svg)](https://circleci.com/gh/dashifyML/dashifyML/tree/master)

## Key Features

### Logging

* Multiprocessing capable logging
* Grid search support out of the box
* ...
### Visualization

* Many tools for deep analysis, such as filtering, aggregation and grouping of metrics
* Filtering of hyperparameters
* ...

### Exports

* Download of plots as .png, .json
* Download of consolidated experiment data as .csv
* Export of the whole dashify analysis and reproduce, continue the analysis at any point later in a different machine too.

## Getting Started

### Install

#### Using pip
```bash
pip install dashifyML
```

#### Alternatively from source
Create a dashify folder, cd into this folder and clone the repository 

``` bash
mkdir dashify_repo
cd dashify_repo
git clone https://github.com/dashifyML/dashifyML.git
```

To install cd into the repository and install the package

``` bash
cd dashifyML
pip install src/
```

### Tracking an experiment
Tracking an experiment is easy as well, as shown in the Listing below. 
First, we have to create a config for our experiment. Then we create an ExperimentInfo object that contains the necessary abstract experiment information regarding the experiment like which model type to train or the base logging directory.
Finally, we can get to run the training function. The `ExperimentTracking` decorator forwards all `stdout` and `stderr` output to a file inside the experiment folder. Additionally, it catches and logs all training routine exceptions, such that during grid search only failing experiment fails and not the entire grid search.

``` python
from dashify.logging.dashify_logging import DashifyLogger, ExperimentTracking, ExperimentInfo

# implement training routine
@ExperimentTracking(log_to_file=False)
def run_training(config: Dict, device=None, experiment_info: ExperimentInfo = None):

  # save the config to disk
  DashifyLogger.save_config(config=config, experiment_info=experiment_info)

  # Run the experiment
  # Note that this block needs to be replaced by the proper training function later one. 
  # Here we just wanted to show how the logging of a metric would work!
  for i in range(config['lower'], config['upper'], config['step_size']):
    # save metric to the metrics dictionary
    metrics_dict = {'loop_metric' : [i]}
    
    # log this metric
    DashifyLogger.log_metrics(experiment_info=experiment_info, metrics=metrics_dict)
    
    
if __name__ == '__main__':
  # define the config
  config = {'lower':10, 'upper':20, 'step_size': 2}
  # creates the necessary folders on disk and returns the experiment information
  experiment_info = DashifyLogger.create_new_experiment(log_dir="dashify_logs",
                                                        subfolder_id="grid_search_1",
                                                        model_name="my_model_1",
                                                        dataset_name="data_set_1",
                                                        run_id=0)
  # execute the training routine                                                   
  run_training(config, "cpu", experiment_info)                                                      
```


### Run the visualization tool

To visualize experiments one just has to run the visualization tool directly from command line.

``` bash
dashify-vis --logdir <your experiments root folder> --port <your port> 
```

Finally, open the URL `127.0.0.1:<your port>` in your browser.

## Troubleshooting

### QT binding issues
In case you a facing 
``` bash
ImportError: Failed to import any qt binding
```
install the mesa-utils via

``` bash
sudo apt-get install mesa-utils
```

## Architecture

## Contribute

We are always looking forward to more people getting involved with this project. If you have questions, feedback, feature requests or bugs please create an issue and we will come back to you. Additionally, if you want to actively contribute codewise, please take a look at our board, where we collect issues in a backlog. If you implemented a feature or fixed a bug, please feel free to write a pull request. 

For merging your branch into dev or master, we employ a two step workflow. Always squash your branch down to a single commit, as described for instance [here](https://blog.carbonfive.com/2017/08/28/always-squash-and-rebase-your-git-commits/). When all tests ran successfully on your branch, please create a pull reqest.

## The Team

DashifyML is developed by Rajkumar Ramamurthy, Max Lübbering, Lars Patrick Hillebrand and Thiago Bell. Our story started in our everyday work at Fraunhofer IAIS, in which were troubled by all the training visualization tools out there. Each of them not giving us the flexibility, scalability that we actually think is needed. Nevetheless, we are convinced that every machine learning training should easily analyzed no matter how complex an algorithm or a grid search gets.

This is why we started started the DashifyML project and herewith, finally open sourced it. 

We are confident that with DashifyML the analysis of machine learning algorithms becomes a great deal easier. 

For contact, please drop us an email: TBD

## License
 
MIT License

Copyright (c) 2019 Max Lübbering, Rajkumar Ramamurthy, Lars Patrick Hillebrand, Thiago Bell 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
