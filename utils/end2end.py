# -*- coding: utf-8 -*-
"""end2end.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kxnj3SLixXVUwUnNSzIJkAdompJjfqEw
"""

import shutil

# shutil.copy("/content/drive/MyDrive/wfh/testJD.zip","/content/")
# shutil.copy("/content/drive/MyDrive/wfh/testResume.zip","/content/")



from pymongo import MongoClient
import fitz
import shutil
from pathlib import Path
import tqdm
from nltk.tokenize import sent_tokenize, word_tokenize
import re
import random
from docx import Document
import nltk
nltk.download('punkt')
import os

from openai import AzureOpenAI
import json
import time

from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch,
    SearchIndex
)

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import ComplexField, SearchIndex

from num2words import num2words
import numpy as np
import tiktoken
from azure.search.documents import SearchClient



def get_all_files(folder_path):
  folder_path =   Path(folder_path)
  all_files = []
  for file_path in folder_path.rglob("*"):
    file_path = str(file_path)
    if ".docx" in file_path or ".pdf" in file_path:
      all_files.append(file_path)
  return all_files

def read_docx(file_path):
    doc = Document(file_path)
    full_text = []
    for paragraph in doc.paragraphs:
      text = paragraph.text
      text = text.replace("\n\n",". ")
      text = text.replace("\n"," ")
      text = ". ".join(["".join(char for char in sent if ord(char)<128) for sent in sent_tokenize(text)])
      text = re.sub(r"[.]+",". ",text)
      full_text.append(text)
    return " ".join(full_text)

def read_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text+=page.get_text()

    #text = re.sub(r"\n",". ",text)
    text = text.replace("\n",". ")
    all_text = ". ".join(["".join(char for char in sent if ord(char)<128) for sent in sent_tokenize(text)])
    all_text = re.sub(r"[.]+",". ",all_text)
    return all_text

def put_raw_data_on_mongodb(mongo_collection,file_paths):
    for file_path in file_paths:
      text_data = None
      if ".docx" in file_path:
        text_data = read_docx(file_path)
      elif ".pdf" in file_path:
        text_data = read_pdf(file_path)

      if text_data is None:
        continue

      file_name = os.path.basename(file_path)
      curr_data = {
        "documentName":file_name,
        "parsedText":text_data
      }
      x = mongo_collection.insert_one(curr_data)

prompt_specifications_jd = """


For the above job description answer the following:

A very short summary of resume?
What is the job title?
What is the job location?
What are the preferred educational qualification?
What are the required skills?
What is the preferred past experience?
What is the required minimum overall years of experience needed in years (numeric only) and field (for example: 4+ years in Records Management, 3+ years in SDE role) (Be specific)?

The answer to above questions should be strictly outputted in json format mentioned below example and if any information not present put "N/A":

{
  "Summary": "Short summary of job description",
	"job title": "Title of job",
	"job location": ["job location1", "job location2"],
	"preferred educational qualification": ["degree in abc", "degree in xyx", "certification in pqr"],
	"required skills": ["skill1", "skill2", "skill3"],
	"preferred past experience": ["4+ years of experience in abc field", "3 years of experience in xyz role","5+ years of experience in pqr industry"],
	"minimum required qualification": ["4+ years of experience in pqr role", "2+ years of experience as mno", "have a degree in abc field"]
}
"""

prompt_specifications_resume = """

For the above resume answer the following:

A very short summary of resume?
What are the Contact Informations (Full Name: Email Address: Phone Number: address)?
What are the Education (Degree name, Institution, Graduation Date) (Be specific)?
What is Work Experience (Job Title, Company Name, Employment Duration, Responsibilities and Achievements ) (Be specific)?
What are candidate's relevant skills (Be specific)?
What are the highlights and accomplishments  (Be specific and if multiple should be separated by ";;")?
What is the Total Years of Experience in numeric?

The answer to above questions should be strictly outputted in json format mentioned below example and if any information not present put "N/A":

{
	"Summary":"Short summary of resume",
	"Contact Information": {
		"Full Name": "",
		"Email Address": "",
		"Phone Number": "",
		"Address": ""
	},
	"Education": [
		{
			"Degree": "",
			"Major/Minor": "",
			"Institution": "",
			"Graduation year": ""
		}
	],
	"Work Experience": [
		{
			"Job Title": "",
			"Company Name": "",
			"Employment Duration": "",
			"Responsibilities and accomplishments": ""
		}
	],
	"Skills":  ["skill1", "skill2", "skill3"],
	"highlights and accomplishments": ["highlight1", "highlight2", "accomplishment1"],
	"Total Years of Experience": "3"
}
"""

prompt_begin_jd = """For the below job description


"""


prompt_begin_resume = """For the below resume


"""

def getAzureClient():
  client = AzureOpenAI(
    azure_endpoint = 'https://sunflower-openai.openai.azure.com/',
    api_key='f68dfd696b2a4917a892e81276af3941',
    api_version="2024-02-01"
  )

  return client

def fix_json(jstring):
  json_string_fixed = jstring.replace(',\n}', '\n}')
  data_dict = json.loads(json_string_fixed)
  return data_dict

def getResponse(client_azure, prompt_begin, context, prompt_specifications):
    prompt = prompt_begin + context + prompt_specifications
    response = client_azure.chat.completions.create(
    model="sunflower", # model = "deployment_name".
    temperature=0.54,  # Set temperature parameter
    max_tokens=2300,
    top_p=0.25,  # Set top_p parameter
    messages=[
      {"role": "user", "content": prompt}
    ]
    )
    try:
      return json.loads(response.choices[0].message.content)
    except:
      try:
        return fix_json(response.choices[0].message.content)
      except:
        return response.choices[0].message.content


def put_gpt_responses_on_mongodb(mongo_collection,prompt_begin,prompt_specifications):
  documents = list(mongo_collection.find({}))
  for curr_data in (documents):
    curr_data["gptResponse"] = getResponse(client_azure, prompt_begin, curr_data['parsedText'],prompt_specifications)
    mongo_collection.update_one({"_id": curr_data["_id"]}, {"$set": curr_data})

def generate_embeddings(text, model="sunflower-embeddings"): # model = "deployment_name"
    if len(text)<2:
      return []
    return client_text_embedding.embeddings.create(input = [text], model=model).data[0].embedding

def create_resume_search_index():
  index_name = "resume-index"

  fields=[
      SimpleField(name="docName", type=SearchFieldDataType.String, key=True,),
      SearchField(name="rawResume", type=SearchFieldDataType.String,
                  searchable=True),
      SearchField(name="summary", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                  searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
      SearchField(name="education", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                  searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
      SearchField(name="workExperience", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                  searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
      SearchField(name="skills", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                  searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
      SearchField(name="highlightsAndAccomplishments", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                  searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
  ]

  #Configure the vector search configuration
  vector_search = VectorSearch(
      algorithms=[
          HnswAlgorithmConfiguration(
              name="myHnsw"
          )
      ],
      profiles=[
          VectorSearchProfile(
              name="myHnswProfile",
              algorithm_configuration_name="myHnsw",
          )
      ]
  )

  index = SearchIndex(name=index_name, fields=fields,
                      vector_search=vector_search)

  # Create the index
  result = client_vec_search.create_or_update_index(index)

  print("Index created:", result)

def create_jd_search_index():
  index_name = "jd-index"

  fields=[
      SimpleField(name="docName", type=SearchFieldDataType.String, key=True,),
      SearchField(name="rawJD", type=SearchFieldDataType.String,
                  searchable=True),
      SearchField(name="summary", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                  searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
      SearchField(name="preferredEducationalQualification", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                  searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
      SearchField(name="preferredSkills", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                  searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
      SearchField(name="preferredPastExperience", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                  searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
      SearchField(name="requiredMinimumQualifications", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                  searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
  ]

  #Configure the vector search configuration
  vector_search = VectorSearch(
      algorithms=[
          HnswAlgorithmConfiguration(
              name="myHnsw"
          )
      ],
      profiles=[
          VectorSearchProfile(
              name="myHnswProfile",
              algorithm_configuration_name="myHnsw",
          )
      ]
  )

  index = SearchIndex(name=index_name, fields=fields,
                      vector_search=vector_search)

  # Create the index
  result = client_vec_search.create_or_update_index(index)

  print("Index created:", result)

stopwords = set([
    "a", "about", "above", "after", "again", "against", "ain", "all", "am",
    "an", "and", "any", "are", "aren", "as", "at", "be", "because",
    "been", "before", "being", "below", "between", "both", "but", "by", "can",
    "couldn", "couldn't", "d", "did", "didn", "didn't", "do", "does", "doesn",
    "doesn't", "doing", "don", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadn", "hadn't", "has", "hasn", "hasn't", "have",
    "haven", "haven't", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "isn", "isn't",
    "it", "it's", "its", "itself", "just", "ll", "m", "ma", "me", "mightn",
    "mightn't", "more", "most", "mustn", "mustn't", "my", "myself", "needn",
    "needn't", "no", "nor", "not", "now", "o", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own",
    "re", "s", "same", "shan", "shan't", "she", "she's", "should", "should've",
    "shouldn", "shouldn't", "so", "some", "such", "t", "than", "that",
    "that'll", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "ve", "very", "was", "wasn", "wasn't", "we", "were", "weren",
    "weren't", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "won", "won't", "wouldn", "wouldn't", "y", "you", "you'd",
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves",
    "could", "he'd", "he'll", "he's", "here's", "how's", "i'd", "i'll", "i'm",
    "i've", "let's", "ought", "she'd", "she'll", "that's", "there's", "they'd",
    "they'll", "they're", "they've", "we'd", "we'll", "we're", "we've",
    "what's", "when's", "where's", "who's", "why's", "would", "able", "abst",
    "accordance", "according", "accordingly", "across", "act", "actually",
    "added", "adj", "affected", "affecting", "affects", "afterwards", "ah",
    "almost", "alone", "along", "already", "also", "although", "always",
    "among", "amongst", "announce", "another", "anybody", "anyhow", "anymore",
    "anyone", "anything", "anyway", "anyways", "anywhere", "apparently",
    "approximately", "arent", "arise", "around", "aside", "ask", "asking",
    "auth", "available", "away", "awfully", "b", "back", "became", "become",
    "becomes", "becoming", "beforehand", "begin", "beginning", "beginnings",
    "begins", "behind", "believe", "beside", "besides", "beyond", "biol",
    "brief", "briefly", "c", "ca", "came", "cannot", "can't", "cause", "causes",
    "certain", "certainly", "co", "com", "come", "comes", "contain",
    "containing", "contains", "couldnt", "date", "different", "done",
    "downwards", "due", "e", "ed", "edu", "effect", "eg", "eight", "eighty",
    "either", "else", "elsewhere", "end", "ending", "enough", "especially",
    "et", "etc", "even", "ever", "every", "everybody", "everyone", "everything",
    "everywhere", "ex", "except", "f", "far", "ff", "fifth", "first", "five",
    "fix", "followed", "following", "follows", "former", "formerly", "forth",
    "found", "four", "furthermore", "g", "gave", "get", "gets", "getting",
    "give", "given", "gives", "giving", "go", "goes", "gone", "got", "gotten",
    "h", "happens", "hardly", "hed", "hence", "hereafter", "hereby", "herein",
    "heres", "hereupon", "hes", "hi", "hid", "hither", "home", "howbeit",
    "however", "hundred", "id", "ie", "im", "immediate", "immediately",
    "importance", "important", "inc", "indeed", "index", "information",
    "instead", "invention", "inward", "itd", "it'll", "j", "k", "keep", "keeps",
    "kept", "kg", "km", "know", "known", "knows", "l", "largely", "last",
    "lately", "later", "latter", "latterly", "least", "less", "lest", "let",
    "lets", "like", "liked", "likely", "line", "little", "'ll", "look",
    "looking", "looks", "ltd", "made", "mainly", "make", "makes", "many", "may",
    "maybe", "mean", "means", "meantime", "meanwhile", "merely", "mg", "might",
    "million", "miss", "ml", "moreover", "mostly", "mr", "mrs", "much", "mug",
    "must", "n", "na", "name", "namely", "nay", "nd", "near", "nearly",
    "necessarily", "necessary", "need", "needs", "neither", "never",
    "nevertheless", "new", "next", "nine", "ninety", "nobody", "non", "none",
    "nonetheless", "noone", "normally", "nos", "noted", "nothing", "nowhere",
    "obtain", "obtained", "obviously", "often", "oh", "ok", "okay", "old",
    "omitted", "one", "ones", "onto", "ord", "others", "otherwise", "outside",
    "overall", "owing", "p", "page", "pages", "part", "particular",
    "particularly", "past", "per", "perhaps", "placed", "please", "plus",
    "poorly", "possible", "possibly", "potentially", "pp", "predominantly",
    "present", "previously", "primarily", "probably", "promptly", "proud",
    "provides", "put", "q", "que", "quickly", "quite", "qv", "r", "ran",
    "rather", "rd", "readily", "really", "recent", "recently", "ref", "refs",
    "regarding", "regardless", "regards", "related", "relatively", "research",
    "respectively", "resulted", "resulting", "results", "right", "run", "said",
    "saw", "say", "saying", "says", "sec", "section", "see", "seeing", "seem",
    "seemed", "seeming", "seems", "seen", "self", "selves", "sent", "seven",
    "several", "shall", "shed", "shes", "show", "showed", "shown", "showns",
    "shows", "significant", "significantly", "similar", "similarly", "since",
    "six", "slightly", "somebody", "somehow", "someone", "somethan",
    "something", "sometime", "sometimes", "somewhat", "somewhere", "soon",
    "sorry", "specifically", "specified", "specify", "specifying", "still",
    "stop", "strongly", "sub", "substantially", "successfully", "sufficiently",
    "suggest", "sup", "sure", "take", "taken", "taking", "tell", "tends", "th",
    "thank", "thanks", "thanx", "thats", "that've", "thence", "thereafter",
    "thereby", "thered", "therefore", "therein", "there'll", "thereof",
    "therere", "theres", "thereto", "thereupon", "there've", "theyd", "theyre",
    "think", "thou", "though", "thoughh", "thousand", "throug", "throughout",
    "thru", "thus", "til", "tip", "together", "took", "toward", "towards",
    "tried", "tries", "truly", "try", "trying", "ts", "twice", "two", "u", "un",
    "unfortunately", "unless", "unlike", "unlikely", "unto", "upon", "ups",
    "us", "use", "used", "useful", "usefully", "usefulness", "uses", "using",
    "usually", "v", "value", "various", "'ve", "via", "viz", "vol", "vols",
    "vs", "w", "want", "wants", "wasnt", "way", "wed", "welcome", "went",
    "werent", "whatever", "what'll", "whats", "whence", "whenever",
    "whereafter", "whereas", "whereby", "wherein", "wheres", "whereupon",
    "wherever", "whether", "whim", "whither", "whod", "whoever", "whole",
    "who'll", "whomever", "whos", "whose", "widely", "willing", "wish",
    "within", "without", "wont", "words", "world", "wouldnt", "www", "x", "yes",
    "yet", "youd", "youre", "z", "zero", "a's", "ain't", "allow", "allows",
    "apart", "appear", "appreciate", "appropriate", "associated", "best",
    "better", "c'mon", "c's", "cant", "changes", "clearly", "concerning",
    "consequently", "consider", "considering", "corresponding", "course",
    "currently", "definitely", "described", "despite", "entirely", "exactly",
    "example", "going", "greetings", "hello", "help", "hopefully", "ignored",
    "inasmuch", "indicate", "indicated", "indicates", "inner", "insofar",
    "it'd", "keep", "keeps", "novel", "presumably", "reasonably", "second",
    "secondly", "sensible", "serious", "seriously", "sure", "t's", "third",
    "thorough", "thoroughly", "three", "well", "wonder", "a", "about", "above",
    "above", "across", "after", "afterwards", "again", "against", "all",
    "almost", "alone", "along", "already", "also", "although", "always", "am",
    "among", "amongst", "amoungst", "amount", "an", "and", "another", "any",
    "anyhow", "anyone", "anything", "anyway", "anywhere", "are", "around", "as",
    "at", "back", "be", "became", "because", "become", "becomes", "becoming",
    "been", "before", "beforehand", "behind", "being", "below", "beside",
    "besides", "between", "beyond", "bill", "both", "bottom", "but", "by",
    "call", "can", "cannot", "cant", "co", "con", "could", "couldnt", "cry",
    "de", "describe", "detail", "do", "done", "down", "due", "during", "each",
    "eg", "eight", "either", "eleven", "else", "elsewhere", "empty", "enough",
    "etc", "even", "ever", "every", "everyone", "everything", "everywhere",
    "except", "few", "fifteen", "fify", "fill", "find", "fire", "first", "five",
    "for", "former", "formerly", "forty", "found", "four", "from", "front",
    "full", "further", "get", "give", "go", "had", "has", "hasnt", "have", "he",
    "hence", "her", "here", "hereafter", "hereby", "herein", "hereupon", "hers",
    "herself", "him", "himself", "his", "how", "however", "hundred", "ie", "if",
    "in", "inc", "indeed", "interest", "into", "is", "it", "its", "itself",
    "keep", "last", "latter", "latterly", "least", "less", "ltd", "made",
    "many", "may", "me", "meanwhile", "might", "mill", "mine", "more",
    "moreover", "most", "mostly", "move", "much", "must", "my", "myself",
    "name", "namely", "neither", "never", "nevertheless", "next", "nine", "no",
    "nobody", "none", "noone", "nor", "not", "nothing", "now", "nowhere", "of",
    "off", "often", "on", "once", "one", "only", "onto", "or", "other",
    "others", "otherwise", "our", "ours", "ourselves", "out", "over", "own",
    "part", "per", "perhaps", "please", "put", "rather", "re", "same", "see",
    "seem", "seemed", "seeming", "seems", "serious", "several", "she", "should",
    "show", "side", "since", "sincere", "six", "sixty", "so", "some", "somehow",
    "someone", "something", "sometime", "sometimes", "somewhere", "still",
    "such", "system", "take", "ten", "than", "that", "the", "their", "them",
    "themselves", "then", "thence", "there", "thereafter", "thereby",
    "therefore", "therein", "thereupon", "these", "they", "thickv", "thin",
    "third", "this", "those", "though", "three", "through", "throughout",
    "thru", "thus", "to", "together", "too", "top", "toward", "towards",
    "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us",
    "very", "via", "was", "we", "well", "were", "what", "whatever", "when",
    "whence", "whenever", "where", "whereafter", "whereas", "whereby",
    "wherein", "whereupon", "wherever", "whether", "which", "while", "whither",
    "who", "whoever", "whole", "whom", "whose", "why", "will", "with", "within",
    "without", "would", "yet", "you", "your", "yours", "yourself", "yourselves",
    "the", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n",
    "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "A", "B", "C",
    "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R",
    "S", "T", "U", "V", "W", "X", "Y", "Z"
])


def remove_stop_words(text,stopwords = stopwords):
    text = text.split()
    text = [w for w in text if not w in stopwords]
    text = " ".join(text)
    return text

def clean_text(x):
    x = x.lower()
    x = remove_stop_words(x)
    x = re.sub('[^a-zA-Z0-9]' , ' ' ,x)
    x =' '.join(x.split())
    return x

def combone_lists(inp_list):
  if type(inp_list)==str:
    return inp_list
  elif type(inp_list)==list:
    processed_list = []
    for curr in inp_list:
      if type(curr) == str:
        if curr.lower() not in ["n/a","not specified","not found"]:
          processed_list.append(curr)
      elif type(curr) == dict:
        processed_list.append(", ".join([key+": "+val for key,val in curr.items() if val.lower() not in ["n/a","not specified","not found"]]))
    return ". ".join(processed_list) + "."
  return ""

def put_embeddings_on_search_client_jd(mongo_collection,index_name,endpoint,credential):
  client_curr_idx = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
  documents = list(mongo_collection.find({}))
  for curr_data in documents:
    documentName = str(curr_data["_id"])
    raw_text = clean_text(curr_data["parsedText"])
    gptResponse = curr_data["gptResponse"]
    summary = generate_embeddings(gptResponse["Summary"])
    peq = generate_embeddings(combone_lists(gptResponse["preferred educational qualification"]))
    rs = generate_embeddings("Required skill for this job are : "+ combone_lists(gptResponse["required skills"]))
    ppe = generate_embeddings("Preferred past experience : "+ combone_lists(gptResponse["preferred past experience"]))
    mrq = generate_embeddings("Minimum required qualification : "+ combone_lists(gptResponse["minimum required qualification"]))
    result = client_curr_idx.upload_documents({"docName":documentName,"rawJD":raw_text,"summary":summary,"preferredEducationalQualification":peq,"preferredSkills":rs,"preferredPastExperience":ppe,"requiredMinimumQualifications":mrq})
def get_chatgpt_esponse(prompt_begin, context, prompt_specifications):
    client_azure = AzureOpenAI(
    azure_endpoint = 'https://sunflower-openai.openai.azure.com/',
    api_key='f68dfd696b2a4917a892e81276af3941',
    api_version="2024-02-01"
    )
    prompt = prompt_begin + context + prompt_specifications
    response = client_azure.chat.completions.create(
    model="sunflower", # model = "deployment_name".
    temperature=0.54,  # Set temperature parameter
    max_tokens=2300,
    top_p=0.25,  # Set top_p parameter
    messages=[
      {"role": "user", "content": prompt}
    ]
    )
    try:
      return json.loads(response.choices[0].message.content)
    except:
      try:
        return fix_json(response.choices[0].message.content)
      except:
        return response.choices[0].message.content
def put_embeddings_on_search_client_resume(mongo_collection,index_name,endpoint,credential):
  client_curr_idx = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
  documents = list(mongo_collection.find({}))
  
  for curr_data in documents:
    documentName = str(curr_data["_id"])
    raw_text = clean_text(curr_data["parsedText"])
    gptResponse = curr_data["gptResponse"]    
    summary = generate_embeddings(gptResponse["Summary"])
    education = generate_embeddings(combone_lists(gptResponse["Education"]))
    workex = generate_embeddings("Work Experience: "+ combone_lists(gptResponse["Work Experience"]))
    skills = generate_embeddings("Skills are: "+ combone_lists(gptResponse["Skills"]))
    haa = generate_embeddings("Highlights and accomplishments: "+ combone_lists(gptResponse["highlights and accomplishments"]))
    result = client_curr_idx.upload_documents({"docName":documentName,"rawResume":raw_text,"summary":summary,"education":education,"workExperience":workex,"skills":skills,"highlightsAndAccomplishments":haa})

CONNECTION_STRING = "mongodb+srv://admin:admin123@sunflowercluster.oppjzec.mongodb.net/"

client_azure =  getAzureClient()

tokenizer = tiktoken.get_encoding("cl100k_base")

client_text_embedding = AzureOpenAI(
  api_key = 'f68dfd696b2a4917a892e81276af3941',
  api_version = "2024-02-01",
  azure_endpoint ='https://sunflower-openai.openai.azure.com/'
)

endpoint_search_client = "https://sunflower-search.search.windows.net/"
admin_key_search_client = "BxtIjEICQtAWR2q5oXLJCl2dX0lGredlN9pev6q65ZAzSeCH3H3Z"

# Create a SearchIndexClient
credential_search_client = AzureKeyCredential(admin_key_search_client)
client_vec_search = SearchIndexClient(endpoint=endpoint_search_client, credential=credential_search_client)

# create_resume_search_index()

# create_jd_search_index()

# put_embeddings_on_search_client_jd(jd_collection,"jd-index",endpoint_search_client,credential_search_client)

# put_embeddings_on_search_client_resume(resume_collection,"resume-index",endpoint_search_client,credential_search_client)