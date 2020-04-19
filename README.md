# Named Entity Recognition Annotator

This repository contains a NER utility to annotate text, given some entities.

![GUI](img/gui.png)

## Installation

To install this GUI you need to make sure that you have `Python 3` on your system.
Then, `cd` into the project's root and run:

```bash
pip install -r requirements.txt
```

This will install the required dependencies (mainly `PyQt5`).

## Usage
To run this utility, make sure you are in the project's root directory and execute the following command:

```bash
python3 annotator.py -o <output> <input> <entities>
```

Here, `<input>` is the path to the input text file, which should contain your training text lines, separated by newlines; `<output>` is the path to where you would like to save the `.json` output file (if not given, it defaults to the same directory as the input file); `<entities>` is the list of entities you would like to annotate.

For example, I could run the program like this:

```bash
python3 annotator.py '~/Desktop/train.txt' 'BirthDate' 'Name'
```

## Output
The utility software will output a `.json` file with the following schema:

```json
[
	{
		"content": "text",
		"entities": [
			[
				0,
				1,
				"entity"
			]
		]
	}
]
```

You can convert this output into the specific format required by your NER model by implementing a function inside the `converter.py` file. Currently, only the `SpaCy` model conversion is provided.  
