import csv
import json
import os
import sys
import datasets
from datasets.tasks import TextClassification


# TODO: Add BibTeX citation
_CITATION = """
TODO: Add citation here
"""

_DESCRIPTION = """
DIFrauD -- (Domain Independent Fraud Detection) is a corpus of deceptive and truthful texts from 7 domains:

"fake_news",
"job_scams",
"phishing",
"political_statements",
"product_reviews",
"sms",
"twitter_rumours"

To load a specific domain, pass it as the "name" parameter to load_dataset()
"""

class DIFrauD(datasets.GeneratorBasedBuilder):
    """Domain Independent Fraud Detection benchmarks -- a Large multi-domain english corpus of truthful and deceptive texts"""

    BUILDER_CONFIGS = [
        datasets.BuilderConfig(name="fake_news", description="Fake News domain"),
        datasets.BuilderConfig(name="job_scams", description="Online Job Scams"),
        datasets.BuilderConfig(name="phishing", description="Email phishing attacks"),
        datasets.BuilderConfig(name="political_statements", description="Statements by various politicians"),
        datasets.BuilderConfig(name="product_reviews", description="Amazon product reviews"),
        datasets.BuilderConfig(name="sms", description="SMS spam and phishing attacks"),
        datasets.BuilderConfig(name="twitter_rumours", 
                               description="Collection of rumours from twitter spanning several years and topics"),
    ]

    DEFAULT_CONFIG_NAME = "phishing"

    def _info(self):
        self.features = datasets.Features(
                {
                    "text": datasets.Value("string"),
                    "label": datasets.ClassLabel(num_classes=2, names=['non-deceptive', 'deceptive']),
                }
        )
        return datasets.DatasetInfo(
            config_name=self.config.name,
            # This is the description that will appear on the datasets page.
            description=_DESCRIPTION,
            # This defines the different columns of the dataset and their types
            features=self.features,  # Here we define them above because they are different between the two configurations
            # If there's a common (input, target) tuple from the features, uncomment supervised_keys line below and
            # specify them. They'll be used if as_supervised=True in builder.as_dataset.
            supervised_keys=("text", "label"),
            # specify standard binary classification task for datasets to setup easier
            task_templates=[TextClassification(text_column="text", label_column="label")],
            # Homepage of the dataset for documentation
            # homepage=_HOMEPAGE,
            # License for the dataset if available
            # license=_LICENSE,
            # Citation for the dataset
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        # TODO: This method is tasked with downloading/extracting the data and defining the splits depending on the configuration
        # If several configurations are possible (listed in BUILDER_CONFIGS), the configuration selected by the user is in self.config.name

        # dl_manager is a datasets.download.DownloadManager that can be used to download and extract URLS
        # It can accept any type or nested list/dict and will give back the same structure with the url replaced with path to local files.
        # By default the archives will be extracted and a path to a cached folder where they are extracted is returned instead of the archive
        urls = {
            "train": self.config.name+"/train.jsonl",
            "test": self.config.name+"/test.jsonl",
            "validation": self.config.name+"/validation.jsonl",
        }
        data_dir = dl_manager.download_and_extract(urls)

        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                # These kwargs will be passed to _generate_examples
                gen_kwargs={
                    "filepath": os.path.join(data_dir['train']),
                    "split": "train",
                },
            ),
            datasets.SplitGenerator(
                name=datasets.Split.VALIDATION,
                gen_kwargs={
                    "filepath": os.path.join(data_dir['validation']),
                    "split": "validation",
                },
            ),
            datasets.SplitGenerator(
                name=datasets.Split.TEST,
                gen_kwargs={
                    "filepath": os.path.join(data_dir['test']),
                    "split": "test"
                },
            ),
        ]

    # method parameters are unpacked from `gen_kwargs` as given in `_split_generators`
    def _generate_examples(self, filepath, split):
        # This method handles input defined in _split_generators to yield (key, example) tuples from the dataset.
        # The `key` is for legacy reasons (tfds) and is not important in itself, but must be unique for each example.
        with open(filepath, encoding="utf-8") as f:
            for key, row in enumerate(f):
                data = json.loads(row)
                yield key, {
                    "text": data["text"],
                    "label": int(data["label"]),
                }

