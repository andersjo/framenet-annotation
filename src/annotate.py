import argparse
import codecs
from collections import defaultdict, Counter
from itertools import groupby
import json
from os.path import expanduser
from flask import Flask, render_template, request, redirect
import sys
import nltk
import re
import framenet
import os

app = Flask(__name__)

def color_map(index):
    colors = ['red', 'green', 'blue', 'yellow', 'orange']
    return colors[index % len(colors)]


def read_sentence(id):
    filename = os.path.join(args.in_dir, id)

    sentence = []
    word_col = None
    pos_col = None

    for token_i, line in enumerate(codecs.open(filename, encoding='utf-8'), 1):
        parts = [part.strip() for part in line.split("\t")]

        # Autodetect file format
        if word_col is None:
            if len(parts) >= 14:
                word_col = 1
                pos_col = 4
            else:
                word_col = 0
                pos_col = 1

        sentence.append({'word': parts[word_col],
                         'pos': parts[pos_col],
                         'frames': filter(None, parts[-1].split(" ")),
                         'token_i': token_i
                         })

    return sentence


def get_annotation_status_by_group():
    annotated_by_group = defaultdict(Counter)
    for fname in os.listdir(args.in_dir):
        if os.path.isfile(os.path.join(args.in_dir, fname)):
            m = re.match("(.*?)(\d+)", fname)
            group_name = m.groups()[0]
            annotated_by_group[group_name]['total'] += 1

    for fname in os.listdir(args.out_dir):
        if os.path.isfile(os.path.join(args.out_dir, fname)):
            m = re.match("(.*?)(\d+)", fname)
            group_name = m.groups()[0]
            if fname.endswith(".invalid"):
                annotated_by_group[group_name]['invalid'] += 1
            else:
                annotated_by_group[group_name]['done'] += 1


    for group_name, stats in annotated_by_group.items():
        stats['done_pct'] = (stats['done'] * 100) / stats['total']
        stats['invalid_pct'] = (stats['invalid'] * 100) / stats['total']
        stats['remaining'] = stats['total'] - stats['invalid'] - stats['done']
        stats['remaining_pct'] = (stats['remaining'] * 100) / stats['total']

    return annotated_by_group

def get_annotation_status():
    annotated = Counter()
    for fname in os.listdir(args.in_dir):
        if os.path.isfile(os.path.join(args.in_dir, fname)):
            annotated['total'] += 1

    for fname in os.listdir(args.out_dir):
        if os.path.isfile(os.path.join(args.out_dir, fname)):
            if fname.endswith(".invalid"):
                annotated['invalid'] += 1
            else:
                annotated['done'] += 1


    annotated['done_pct'] = (annotated['done'] * 100) / annotated['total']
    annotated['invalid_pct'] = (annotated['invalid'] * 100) / annotated['total']
    annotated['remaining'] = annotated['total'] - annotated['invalid'] - annotated['done']
    annotated['remaining_pct'] = (annotated['remaining'] * 100) / annotated['total']

    return annotated    
    

@app.route("/annotate/save/<id>", methods=['POST'])
def save_sentence(id=None):
    sentence = read_sentence(id)

    out = codecs.open(os.path.join(args.out_dir, id), 'w', encoding='utf-8')
    for i, token in enumerate(sentence, 1):
        frame_name = None
        arguments = {}

        if len(token['frames']) > 0:
            selected_frame = request.form['select-{}'.format(i)]
            if selected_frame:
                frame_name = selected_frame.split("-")[1]
                # Grab arguments
                for key, val in request.form.items():
                    if key.startswith(selected_frame) and val:
                        arguments[key.split("-")[2]] = val


        parts = map(unicode, [token['token_i'], token['word'], token['pos'], frame_name or '', json.dumps(arguments)])
        print >>out, u"\t".join(parts)

    out.close()

    return "OK"


@app.route("/mark_as_error/<id>")
def mark_as_error(id=None):
    next_id_index = sentence_ids.index(id) + 1
    next_id = sentence_ids[next_id_index] if next_id_index < len(sentence_ids) else None

    filename = os.path.join(args.out_dir, id)
    if os.path.isfile(filename):
        os.remove(filename)

    filename += ".invalid"
    open(filename, 'w').close()

    return redirect("/annotate/{}".format(next_id), code=302)


@app.route("/annotation_status")
def annotation_status():
    return render_template('annotation_status.html', annotated_by_group=get_annotation_status_by_group())


@app.route("/annotate/<id>")
def annotate_sentence(id=None):
    sentence = read_sentence(id)
    next_id_index = sentence_ids.index(id) + 1
    next_id = sentence_ids[next_id_index] if next_id_index < len(sentence_ids) else None

    pre_annotations = []
    for i, token in enumerate(sentence):
        if len(token['frames']) > 0:
            pre_annotation= {'token': token,
                             'frames': [],
                             'i': token['token_i'],
                             'color': color_map(i)}
            for frame_name in token['frames']:
                frame = fnet.frame_by_name(frame_name)
                frame_elems_by_type = defaultdict(list)
                for fe in frame.FE.values():
                    fe.abbrev = fe.abbrev or fe.name[0:3]
                    frame_elems_by_type[fe.coreType].append(fe)
                pre_annotation['frames'].append({'name': frame.name,
                                                 'definition': frame.definition,
                                                 'fe_by_type': frame_elems_by_type})
            pre_annotations.append(pre_annotation)


    return render_template('annotate.html',
                           sentence=sentence, pre_annotations=pre_annotations,
                           id=id, next_id=next_id,
                           annotation_status=get_annotation_status())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""A web interface for annotating Framenet across languages""")
    parser.add_argument('in_dir', help="Directory with input files, each containing a single sentence in tab separated format."
                                      "The last column contains a list of space-separated list of possible frames evoked by that token")
    parser.add_argument('out_dir', help="Directory for finished annotations")

    args = parser.parse_args()

    def find_framenet():
        for path in nltk.data.path:
            candidate = os.path.join(path, os.path.join('corpora', 'framenet_v15'))

            if os.path.isdir(candidate):
                return candidate

    framenet_data = find_framenet()
    if not framenet_data:
        nltk.download('framenet_v15')
        framenet_data = find_framenet()

    fnet = framenet.FramenetCorpusReader(framenet_data, [])

    sentence_ids = [fname for fname in os.listdir(args.in_dir)
                    if os.path.isfile(os.path.join(args.in_dir, fname))]

    annotated_sentence_ids = [fname for fname in os.listdir(args.out_dir)
                              if os.path.isfile(os.path.join(args.out_dir, fname))]

    unannotated_sentence_ids = list(sorted(set(sentence_ids) - set(annotated_sentence_ids)))

    if unannotated_sentence_ids:
        first_sentence_id = unannotated_sentence_ids[0]
    else:
        print "WARNING. All sentences have been annotated. Restarting the annotation at the beginning."
        first_sentence_id = sentence_ids[0]

    print >>sys.stderr, "{} sentences found, of which {} are not yet annotated.".format(len(sentence_ids), len(unannotated_sentence_ids))
    print >>sys.stderr, "Web server started. Navigate to\n\n\thttp://127.0.0.1:5000/annotate/{} \n\nto get started".format(first_sentence_id)


    # Start the web server
    # app.run(debug=True)
    app.run()
