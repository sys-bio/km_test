"""
=============================================
Embedding in a web application server (Flask)
=============================================

When using Matplotlib in a web server it is strongly recommended to not use
pyplot (pyplot maintains references to the opened figures to make
`~.matplotlib.pyplot.show` work, but this will cause memory leaks unless the
figures are properly closed).

Since Matplotlib 3.1, one can directly create figures using the `.Figure`
constructor and save them to in-memory buffers.  In older versions, it was
necessary to explicitly instantiate an Agg canvas (see e.g.
:doc:`/gallery/user_interfaces/canvasagg`).

The following example uses Flask_, but other frameworks work similarly:

.. _Flask: https://flask.palletsprojects.com

"""
import sys
import os.path
import argparse



sys.path.append('E:\\Research\\sys-bio\\SBviper')
sys.path.append('E:\\Research\\sys-bio\\SBviper\\SBviper')
from viper_dynamic.util import *
from SBviper.SBviper.viper_dynamic.constants import get_filter
from viper_dynamic.matcher.time_series_matcher import TimeSeriesMatcher
from viper_dynamic.constants import str_to_function
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

import base64
from io import BytesIO

from flask import Flask, render_template, request, jsonify, send_file
from matplotlib.figure import Figure

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/pic")
def hello():
    # Generate the figure **without using pyplot**.
    fig = Figure()
    ax = fig.subplots()
    ax.plot([1, 2])
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"<img src='data:image/png;base64,{data}'/>"


@app.route("/run", methods=['POST'])
def run():
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(APP_ROOT, 'fileDB')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    original_path_origin = request.files['original-file']
    original_path_origin.save(os.path.join(app.config['UPLOAD_FOLDER'], original_path_origin.filename))
    revised_path_origin = request.files['revised-file']
    revised_path_origin.save(os.path.join(app.config['UPLOAD_FOLDER'], revised_path_origin.filename))
    path_1 = request.form.get("file-type-1")
    path_2 = request.form.get("file-type-2")
    print(path_1)
    print(path_2)
    original_path = "E:\\Research\\sys-bio\\SBviper\\fileDB\\" + original_path_origin.filename
    revised_path = "E:\\Research\\sys-bio\\SBviper\\fileDB\\" + revised_path_origin.filename
    # path = 'Antimony'
    # original_path = "E:\\Research\\sys-bio\\SBviper\\tests\\experiments\\model_ant_original.txt"
    # revised_path = 'E:\\Research\\sys-bio\\SBviper\\tests\\experiments\\model_ant_original.txt'
    if path_1 == "SBML":
        # TODO: Test this
        original_tsc, temp1 = get_tsc_from_SBML(original_path,
                                                      original_path)
    elif path_1 == "CSV":
        # TODO: Test this
        original_tsc, temp1 = get_tsc_from_CSV(original_path,
                                                     original_path)
    else:  # Antimony
        original_tsc, temp1 = get_tsc_from_Ant(original_path,
                                                     original_path)
    if path_2 == "SBML":
        # TODO: Test this
        revised_tsc, temp2 = get_tsc_from_SBML(revised_path,
                                                      revised_path)
    elif path_2 == "CSV":
        # TODO: Test this
        revised_tsc, temp2 = get_tsc_from_CSV(revised_path,
                                                     revised_path)
    else:  # Antimony
        revised_tsc, temp2 = get_tsc_from_Ant(revised_path,
                                                     revised_path)

    filters = request.form.get("frechet-distance")
    tolerance_value = request.form.get("tolerance")
    matcher = TimeSeriesMatcher(original_tsc, revised_tsc)
    # add filters to matcher
    if filters != None:
        filters = filters.split()
        for filter_str in filters:
            if filter_str in str_to_function:
                matcher.add_filter(get_filter(filter_str, tolerance_value))
            else:
                print(filter_str + " does not exist!")
    # run filters
    filtered_collection, non_filtered_collection = matcher.run()

    # show result

    fig, axs = plt.subplots(ncols=2, nrows=len(filtered_collection) +
                                           len(non_filtered_collection), figsize=(15, 15))
    plt.subplots_adjust(0.125, 0.1, 0.9, 0.9, 0.2, 1.5)
    index = 0
    for match_results in filtered_collection.match_results:
        if match_results.original_ts is not None:
            axs[index, 0].plot(match_results.original_ts.time_points,
                               match_results.original_ts.values, color="#257F5E")
            axs[index, 0].set_title("Filtered: Original " +
                                    match_results.original_ts.variable)
        if match_results.revised_ts is not None:
            axs[index, 1].plot(match_results.revised_ts.time_points,
                               match_results.revised_ts.values, color="#8F6C05")
            axs[index, 1].set_title("Filtered: Revised " +
                                    match_results.revised_ts.variable)
        index += 1
    for match_results in non_filtered_collection.match_results:
        print("A")
        if match_results.original_ts is not None:
            axs[index, 0].plot(match_results.original_ts.time_points,
                               match_results.original_ts.values, color="#0330fc")
            axs[index, 0].set_title("Non-Filtered: Original " +
                                    match_results.original_ts.variable)
        if match_results.revised_ts is not None:
            axs[index, 1].plot(match_results.revised_ts.time_points,
                               match_results.revised_ts.values, color="#fc0303")
            axs[index, 1].set_title("Non-Filtered: Revised " +
                                    match_results.revised_ts.variable)
        index += 1
    fig.savefig('images/all/' + 'all.png', format="png")
    plt.close(1)
    filtered_result = []
    figureCount = 2
    for match_results in filtered_collection.match_results:
        if match_results.original_ts is not None:
            figureCount += 1
            fig = plt.figure(figureCount)
            plt.plot(match_results.original_ts.time_points,
                     match_results.original_ts.values, color="#257F5E")
            fig.suptitle("Filtered: Original " +
                         match_results.original_ts.variable)
            fig.savefig('images/filtered/filtered_original_' + match_results.original_ts.variable + '.png', format="png")
            filtered_result.append(
                ['filtered_original_' + match_results.original_ts.variable + '.png', match_results.original_ts.variable])
            plt.close(figureCount)
        if match_results.revised_ts is not None:
            figureCount += 1
            fig = plt.figure(figureCount)
            plt.plot(match_results.revised_ts.time_points,
                     match_results.revised_ts.values, color="#8F6C05")
            fig.suptitle("Filtered: Revised " +
                         match_results.revised_ts.variable)
            fig.savefig('images/filtered/filtered_revised_' + match_results.revised_ts.variable + '.png', format="png")
            filtered_result.append(
                ['filtered_revised_' + match_results.revised_ts.variable + '.png', match_results.revised_ts.variable])
            plt.close(figureCount)

    non_filtered_result = []
    for match_results in non_filtered_collection.match_results:
        if match_results.original_ts is not None:
            figureCount += 1
            fig = plt.figure(figureCount)
            plt.plot(match_results.original_ts.time_points,
                     match_results.original_ts.values, color="#0330fc")
            fig.suptitle("Non-Filtered: Original " +
                         match_results.original_ts.variable)
            fig.savefig('images/non_filtered/non_filtered_original_' + match_results.original_ts.variable + '.png',
                        format="png")
            non_filtered_result.append(['non_filtered_original_' + match_results.original_ts.variable + '.png',
                                        match_results.original_ts.variable])
            plt.close(figureCount)
        if match_results.revised_ts is not None:
            figureCount += 1
            fig = plt.figure(figureCount)
            plt.plot(match_results.revised_ts.time_points,
                     match_results.revised_ts.values, color="#fc0303")
            fig.suptitle("Non-Filtered: Revised " +
                         match_results.revised_ts.variable)
            fig.savefig('images/non_filtered/non_filtered_revised_' + match_results.revised_ts.variable + '.png',
                        format="png")
            non_filtered_result.append(
                ['non_filtered_revised_' + match_results.revised_ts.variable + '.png', match_results.revised_ts.variable])
            plt.close(figureCount)
    all_result = ["all.png", 'all']
    combined_result = {"filtered": filtered_result, "non-filtered": non_filtered_result, "all": all_result}
    return jsonify(combined_result)


@app.route("/images/<section1>/<section2>", methods=['GET'])
def get_image(section1, section2):
    filename = request.path[1:]
    return send_file(filename, mimetype='image/png')

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r
#############################################################################
#
# Since the above code is a Flask application, it should be run using the
# `flask command-line tool <https://flask.palletsprojects.com/en/master/cli/>`_
# Assuming that the working directory contains this script:
#
# Unix-like systems
#
# .. code-block:: console
#
#  FLASK_APP=web_application_server_sgskip flask run
#
# Windows
#
# .. code-block:: console
#
#  set FLASK_APP=app
#  flask run
#
#
# Clickable images for HTML
# -------------------------
#
# Andrew Dalke of `Dalke Scientific <http://www.dalkescientific.com>`_
# has written a nice `article
# <http://www.dalkescientific.com/writings/diary/archive/2005/04/24/interactive_html.html>`_
# on how to make html click maps with Matplotlib agg PNGs.  We would
# also like to add this functionality to SVG.  If you are interested in
# contributing to these efforts that would be great.
