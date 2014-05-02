# Framenet annotation

This is a browser-based tool for annotating sentences with Framenet 1.5 frames and arguments.
It starts a web server, which runs on your local computer and is only accessible from there.

As input the tool accepts a folder of tab-separated files with one token per line and one sentence per file.
 The final column is a space-separated list of frames that could be triggered by that token.
 The output looks like the input, except the last column has been replaced by the annotations selected in the interface.
 Saving the annotations happens automatically in the background.

Here is an example of the input format (see `data/demo/ritter.dev01`):

```
But     CONJ
in      ADP
any     DET
case    NOUN    Instance Reasoning Containers Trial
I       PRON
suppose VERB    Opinion
you     PRON
will    VERB    Giving Desiring
not     ADV
let     VERB    Grant_permission Make_possible_to_do
it      PRON
away    ADV
for     ADP
some    DET
days    NOUN    Calendric_unit Timespan Measure_duration
?       .
```

The CONLL9 format, where the word is in the second column and the part of speech is in the fourth column, is also supported.
It will be automatically selected if the number of input columns is equal to 14.


## Installation

The annotation tool is written in Python and depends on the web framework `flask` as well as a fairly recent version of `NLTK`.

Install the dependencies via `pip`:

```
pip install -r requirements.txt
```

The tool also uses the Framenet data distributed by NLTK. It looks for the data in `$HOME/nltk_data/corpora/framenet_v15`,
which is the default install location used by NLTK. If the data is not found, the tool will attempt to download it using NLTK.
Unfortunately, this will fail if your NLTK data is in a non-standard location.

## Usage

To run the demo, type `% python src/annotate.py data/demo .`. This puts the annotated files in the current directory.

To access the web interface go to `http://127.0.0.1:5000/annotate/ritter.dev01`.

The command line options are:


```
usage: annotate.py [-h] in_dir out_dir

A web interface for annotating Framenet across languages

positional arguments:
  in_dir      Directory with input files, each containing a single sentence in
              tab separated format.The last column contains a list of space-
              separated list of possible frames evoked by that token
  out_dir     Directory for finished annotations

optional arguments:
  -h, --help  show this help message and exit
```


## Caveat

In the current version, visiting a sentence in the browser that has already been annotated will overwrite the existing annotation.