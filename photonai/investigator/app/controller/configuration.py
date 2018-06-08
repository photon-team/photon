from flask import render_template, request
from photonai.investigator.app.main import app
from photonai.validation.ResultsDatabase import MDBHyperpipe
from pymodm.errors import ValidationError, ConnectionError
from photonai.investigator.app.model.PlotlyTrace import PlotlyTrace
from photonai.investigator.app.model.PlotlyPlot import PlotlyPlot
from photonai.investigator.app.model.ConfigItem import ConfigItem
from photonai.investigator.app.model.Config import Config


@app.route('/pipeline/<name>/outer_fold/<fold_nr>/compare_configurations', methods=['POST'])
def compare_configurations(name, fold_nr):
    try:
        selected_config_nr_list = request.form.getlist('config_list')

        config_dict_list = list()
        config_list = list()
        trace_training_list = list()
        trace_test_list = list()

        pipe = MDBHyperpipe.objects.get({'name': name})
        outer_fold = pipe.outer_folds[int(fold_nr) - 1]

        for config in outer_fold.tested_config_list:
            if str(config.config_nr) in selected_config_nr_list:
                config_dict = Config('config_' + str(config.config_nr))
                config_list.append(config)

                trace_training = PlotlyTrace('config_' + str(config.config_nr), '', 'bar')
                trace_test = PlotlyTrace('config_' + str(config.config_nr), '', 'bar')

                for train in config.metrics_train:
                    if train.operation == 'FoldOperations.MEAN':
                        trace_training.add_x(str(train.metric_name))
                        trace_training.add_y(train.value)
                for test in config.metrics_test:
                    if test.operation == 'FoldOperations.MEAN':
                        trace_test.add_x(str(test.metric_name))
                        trace_test.add_y(test.value)
                trace_training_list.append(trace_training)
                trace_test_list.append(trace_test)

                for key, value in config.config_dict.items():
                    config_item = ConfigItem(str(key), str(value))
                    config_dict.add_item(config_item)
                config_dict_list.append(config_dict)

        plot_training = PlotlyPlot('comparison_metrics_training', 'train metrics of selected configurations', trace_training_list)
        plot_test = PlotlyPlot('comparison_metrics_test', 'test metrics of selected configurations', trace_test_list)

        return render_template('configuration/compare.html', pipe=pipe, outer_fold=outer_fold
                               , plot_test=plot_test
                               , plot_training=plot_training
                               , config_dict_list=config_dict_list)

    except ValidationError as exc:
        return exc.message
    except ConnectionError as exc:
        return exc.message