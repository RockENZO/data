---
language:
- en
license:
- mit
size_categories:
- 10K<n<100K
multilinguality:
- monolingual
task_categories:
- text-classification
- zero-shot-classification
pretty_name: DIFrauD - Domain-Independent Fraud Detection benchmark
tags:
- fraud-detection
- deception-detection
- phishing
- fake-news
- benchmark
- opinion-spam
- multi-domain
configs:
- config_name: fake_news
  data_files:
  - split: train
    path: fake_news/train.jsonl
  - split: test
    path: fake_news/test.jsonl
  - split: validation
    path: fake_news/validation.jsonl
- config_name: job_scams
  data_files:
  - split: train
    path: job_scams/train.jsonl
  - split: test
    path: job_scams/test.jsonl
  - split: validation
    path: job_scams/validation.jsonl
- config_name: phishing
  data_files:
  - split: train
    path: phishing/train.jsonl
  - split: test
    path: phishing/test.jsonl
  - split: validation
    path: phishing/validation.jsonl
- config_name: political_statements
  data_files:
  - split: train
    path: political_statements/train.jsonl
  - split: test
    path: political_statements/test.jsonl
  - split: validation
    path: political_statements/validation.jsonl
- config_name: product_reviews
  data_files:
  - split: train
    path: product_reviews/train.jsonl
  - split: test
    path: product_reviews/test.jsonl
  - split: validation
    path: product_reviews/validation.jsonl
- config_name: sms
  data_files:
  - split: train
    path: sms/train.jsonl
  - split: test
    path: sms/test.jsonl
  - split: validation
    path: sms/validation.jsonl
- config_name: twitter_rumours
  data_files:
  - split: train
    path: twitter_rumours/train.jsonl
  - split: test
    path: twitter_rumours/test.jsonl
  - split: validation
    path: twitter_rumours/validation.jsonl
---

# DIFrauD - Domain Independent Fraud Detection Benchmark

Domain Independent Fraud Detection Benchmark is a labeled corpus containing over 95,854 samples of deceitful 
and truthful texts from a number of independent domains and tasks. Deception, however, can be different --
in this corpus we made sure to gather strictly real examples of deception that are intentionally malicious 
and cause real harm, despite them often having very little in common. Covering seven domains, this benchmark 
is designed to serve as a representative slice of the various security challenges that remain open problems
today.


## DATASET 

The entire dataset contains 95854 samples, 37282 are deceptive and 58572 non-deceptive.

There are 7 independent domains in the dataset.

Each task is (or has been converted to) a binary classification problem where `y` is an indicator of deception.

1) **Phishing** (2020 Email phishing benchmark with manually labeled emails) 

   *- total: 15272 deceptive: 6074 non-deceptive: 9198*

2) **Fake News** (News Articles)

   *- total: 20456 deceptive: 8832 non-deceptive: 11624*

3) **Political Statements** (Claims and statements by politicians and other entities, made from Politifact by relabeling LIAR)

   *- total: 12497 deceptive: 8042 non-deceptive: 4455*

4) **Product Reviews** (Amazon product reviews)

   *- total: 20971 deceptive: 10492 non-deceptive: 10479*

5) **Job Scams** (Job postings on an online board)

   *- total: 14295 deceptive: 599 non-deceptive: 13696*

6) **SMS** (combination of SMS Spam from UCI repository and SMS Phishing datasets)

    *- total: 6574 deceptive: 1274 non-deceptive: 5300*

7) **Twitter Rumours** (Collection of rumours from PHEME dataset, covers multiple topics)
   
    *- total: 5789 deceptive: 1969 non-deceptive: 3820*

Each one was constructed from one or more datasets. Some tasks were not initially binary and had to be relabeled. 
The inputs vary wildly both stylistically and syntactically, as well as in terms of the goal of deception 
(or absence of thereof) being performed in the context of each dataset. Nonetheless, all seven datasets contain a significant
fraction of texts that are meant to deceive the person reading them one way or another.

Each subdirectory/config contains the domain/individual dataset split into three files:

`train.jsonl`, `test.jsonl`, and `validation.jsonl` 

that contain train, test, and validation sets, respectively.

The splits are:

-- train=80%

-- test=10%

-- valid=10%

The sampling process was random with seed=42. It was stratified with respect to `y` (label) for each domain.

### Fields

Each `jsonl` file has two fields (columns): `text` (string) and `label` (integer)

`text` contains a statement or a claim that is either deceptive or thruthful. 
It is guaranteed to be valid unicode, less than 1 million characters, and contains no empty entries or non-values.

`label` answers the question whether text is deceptive: `1` means yes, it is deceptive, `0` means no, 
the text is not deceptive (it is truthful).

### Processing and Cleaning

Each dataset has been cleaned using Cleanlab. Non-english entries, erroneous (parser error) entries, empty entries, duplicate entries, 
entries of length less than 2 characters or exceeding 1000000 characters were all removed.

Labels were manually curated and corrected in cases of clear error. 

Whitespace, quotes, bulletpoints, unicode is normalized.

### Layout

The directory layout of `difraud` is like so:

``
difraud
  fake_news/
    train.jsonl
    test.jsonl
    validation.jsonl
    README.md
  ...
  ...
  ...
  sms/
    train.jsonl
    test.jsonl
    validation.jsonl
    README.md
  README.md
  LICENSE.txt
``

### Documentation

Primary documentation is this README file. Each dataset's directory contains a `README.md` file with additional details. 
The contents of these files are also included at the end of this document in the Appendix. 
LICENSE.txt contains the MIT license this dataset is distributed under.

## CHANGES

This dataset is a successor of [the GDD dataset](https://zenodo.org/record/6512468). 

Noteable changes from GDD are:

1) Addition of SMS and Twitter Rumours datasets, making it 7 deception datasets from different domains in total

2) Re-labeling of Political Statements dataset using a scheme that better fits with prior published work that used it and is stricter in terms of non-deceptive statement criteria of acceptance (see the README file specific to the dataset within its directory)

3) Job Scams datasets' labeles were previously inverted, with ~13500 labeled as deceptive (is_deceptive=True) and ~600 as non-deceptive. This could lead to potential issues with using metrics such as f1-score, which for binary classification is computed for the class considered to be positive. This issue has been addressed and the deceptive texts are labeled as 1 (e.g. positive or True) while non-deceptive as 0 (e.g. negative or False)

4) All datasets have been processed using Cleanlab, with problematic samples maually examined and issues addressed if needed. See the details in each of the individual datasets README files.

5) All datasets now come in 2 formats: the entirety of the data in a single jsonl file located in the `data/` subdirectory of each dataset, and a standard train-test-valid stratified split of 80-10-10, in 3 separate jsonl files.

6) All datasets have two fields: "text" (string) and "label" (integer, 0 or 1 - 0 indicates that the text is non-deceptive, 1 means it is deceptive)

7) '\n' has been normalized to ' ' for all datasets as it causes issues with BERT's tokenizer in some cases (and to be in line with general whitespace normalization). Broken unicode has been fixed. Whitespace, quotations, and bullet points were normalized. Text is limited to 1,000,000 characters in length and guaranteed to be non-empty. Duplicates within the the same dataset (even in text only) were dropped, so were empty and None values. 

## LICENSE

This dataset is published under the MIT license and can be used and modified by anyone free of charge. 
See LICENSE.txt file for details. 

## CITING

If you found this dataset useful in your research, please consider citing it as:

TODO: ADD our paper reference

## REFERENCES 

Original GDD paper:

@inproceedings{10.1145/3508398.3519358,
author = {Zeng, Victor and Liu, Xuting and Verma, Rakesh M.},
title = {Does Deception Leave a Content Independent Stylistic Trace?},
year = {2022},
isbn = {9781450392204},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3508398.3519358},
doi = {10.1145/3508398.3519358},
abstract = {A recent survey claims that there are em no general linguistic cues for deception. Since Internet societies are plagued with deceptive attacks such as phishing and fake news, this claim means that we must build individual datasets and detectors for each kind of attack. It also implies that when a new scam (e.g., Covid) arrives, we must start the whole process of data collection, annotation, and model building from scratch. In this paper, we put this claim to the test by building a quality domain-independent deception dataset and investigating whether a model can perform well on more than one form of deception.},
booktitle = {Proceedings of the Twelfth ACM Conference on Data and Application Security and Privacy},
pages = {349–351},
numpages = {3},
keywords = {domain-independent deception detection, dataset quality/cleaning},
location = {Baltimore, MD, USA},
series = {CODASPY '22}
}

## APPENDIX: Dataset and Domain Details

This section describes each domain/dataset in greater detail.

### FAKE NEWS

Fake News used WELFake as a basis. The WELFake dataset combines 72,134 news articles from four pre-existing datasets 
(Kaggle, McIntire, Reuters, and BuzzFeed Political). The dataset was cleaned of data leaks in the form of citations of 
often reputable sources, such as "[claim] (Reuters)". It contains 35,028 real news articles and 37,106 fake news articles. 
We found a number of out-of-domain statements that are clearly not relevant to news, such as "Cool", which is a potential
problem for transfer learning as well as classification. 

The training set contains 16364 samples, the validation and the test sets have 2064 and 2064 samles, respectively.

### JOB SCAMS

The Employment Scam Aegean Dataset, henceforth referred to as the Job Scams dataset, consisted of 17,880 human-annotated job listings of
job descriptions labeled as fraudulent or not.

#### Relabeling

The original Job Labels dataset had the labels inverted when released. The problem is now fixed, the labels are correct.

#### Cleaning 

It was cleaned by removing all HTML tags, empty descriptions, and duplicates. 
The final dataset is heavily imbalanced, with 599 deceptive and 13696 non-deceptive samples out of the 14295 total.

### PHISHING

This dataset consists of various phishing attacks as well as benign emails collected from real users.

The training set contains 12217 samples, the validation and the test sets have 1527 and 1528 samples, respectively.

### POLITICAL STATEMENTS

This corpus was created from the Liar dataset which consists of political statements made by US speakers assigned
a fine-grain truthfulness label by PolitiFact.

#### Labeling

The primary difference is the change in the re-labeling scheme when converting the task from multiclass to binary. 

#### Old scheme

We use the claim field as the text and map labels “pants-fire,” “false,”
“barely-true,” to deceptive and “half-true,” “mostly-true,” and “true”
to non-deceptive, resulting in 5,669 deceptive and 7,167 truthful
statements. 

#### New scheme

Following 

*Upadhayay, B., Behzadan, V.: "Sentimental liar: Extended corpus and deep learning models for fake claim classification" (2020)*

and

*Shahriar, Sadat, Arjun Mukherjee, and Omprakash Gnawali. "Deception Detection with Feature-Augmentation by Soft Domain Transfer." 
International Conference on Social Informatics. Cham: Springer International Publishing, 2022.*

we map the labels  map labels “pants-fire,” “false,”
“barely-true,” **and “half-true,”** to deceptive; the labels "mostly-true" and "true" are mapped to non-deceptive. 
The statements that are only half-true are now considered to be deceptive, making the criterion for statement being non-deceptive stricter: 
now 2 out of 6 labels map to non-deceptive and 4 map to deceptive.

#### Cleaning

The dataset has been cleaned using cleanlab with visual inspection of problems found. Partial sentences, such as "On Iran nuclear deal", 
"On inflation", were removed. Text with large number of errors induced by a parser were also removed.
Statements in language other than English (namely, Spanish) were also removed. 

The training set contains 9997 samples, the validation and the test sets have 1250 samples each in them.

### PRODUCT REVIEWS

The dataset is produced from English Amazon Reviews labeled as either real or fake, relabeled as deceptive and non-deceptive respectively. 
The reviews cover a variety of products with no particular product dominating the dataset. Although the dataset authors filtered out 
non-English reviews, through outlier detection we found that the dataset still contains reviews in Spanish and other languages. 
Problematic label detection shows that over 6713 samples are potentially mislabeled; since this technique is error-prone,
we visually examine 67 reviews that are found to be the largest potential sources of error (the top percentile) and confirm that
most of them appear to be mislabeled. The final dataset of 20,971 reviews is evenly balanced with 10,492 deceptive and 10,479 
non-deceptive samples.

The training set contains 16776 samples, the validation and the test sets have 2097 and 2098 samples, respectively.

### SMS

This dataset was created from the SMS Spam Collection and SMS Phishing Dataset for Machine Learning and Pattern Recognition, 
which contained 5,574 and 5,971 real English SMS messages, respectively. As these two datasets overlap, after de-duplication, 
the final dataset is made up of 6574 texts released by a private UK-based wireless operator; 1274 of them are deceptive, 
and the remaining 5300 are not.

The training set contains 5259 samples, the validation and the test sets have 657 and 658 samples, 
respectively.

### TWITTER RUMOURS

This deception dataset was created using PHEME dataset from 

https://figshare.com/articles/dataset/PHEME_dataset_of_rumours_and_non-rumours/4010619/1

was used in creation of this dataset. We took source tweets only, and ignored replies to them. 
We used source tweet's label as being a rumour or non-rumour to label it as deceptive or non-deceptive.

The training set contains 4631 samples, the validation and the test sets have 579 samples each

## Citation Information

If you use any of these resources, please cite our dataset DIFrauD paper:

    @inproceedings{boumber-etal-2024-domain,
    title = "Domain-Agnostic Adapter Architecture for Deception Detection: Extensive Evaluations with the {DIF}rau{D} Benchmark",
    author = "Boumber, Dainis A.  and Qachfar, Fatima Zahra  and Verma, Rakesh",
    editor = "Calzolari, Nicoletta  and Kan, Min-Yen  and Hoste, Veronique  and Lenci, Alessandro  and Sakti, Sakriani  and Xue, Nianwen",
    booktitle = "Proceedings of the 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation (LREC-COLING 2024)",
    month = may,
    year = "2024",
    address = "Torino, Italia",
    publisher = "ELRA and ICCL",
    url = "https://aclanthology.org/2024.lrec-main.468",
    pages = "5260--5274"}