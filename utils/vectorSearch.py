from openai import AzureOpenAI
import json
from azure.search.documents.models import VectorizedQuery
from nltk.tokenize import sent_tokenize, word_tokenize
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from pymongo import MongoClient
import math

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

def get_chatgpt_response(prompt_begin, context, prompt_specifications):
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

import regex as re
from bson import ObjectId
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

def generate_embeddings(text, model="sunflower-embeddings"): # model = "deployment_name"
    if len(text)<2:
      return []
    return client_text_embedding.embeddings.create(input = [text], model=model).data[0].embedding


def search_resume_text_summary_embedd(text, top_k):
  text_embedd = generate_embeddings(text)
  text = clean_text(text)
  vector_query_summary = VectorizedQuery(vector=text_embedd, k_nearest_neighbors=top_k, fields="summary")

  results = client_search_resume.search(
      search_text=text,
      vector_queries= [vector_query_summary],
      select=["docName"],
  )
  return results

def get_file_name_from_mongo(mongo_collection,doc_id):
  doc_id = ObjectId(doc_id)
  result = mongo_collection.find_one({"_id": doc_id})
  return result["documentName"]

def serach_resume_all_embedd(text, top_k):
  gptResponse = get_chatgpt_response(prompt_begin_jd, text ,prompt_specifications_jd)
  summary = generate_embeddings(gptResponse["Summary"])
  peq = generate_embeddings(combone_lists(gptResponse["preferred educational qualification"]))
  rs = generate_embeddings("Required skill for this job are : "+ combone_lists(gptResponse["required skills"]))
  ppe = generate_embeddings("Preferred past experience : "+ combone_lists(gptResponse["preferred past experience"]))
  mrq = generate_embeddings("Minimum required qualification : "+ combone_lists(gptResponse["minimum required qualification"]))

  vector_query_summary = VectorizedQuery(vector=summary, k_nearest_neighbors=top_k, fields="summary")
  vector_query_education = VectorizedQuery(vector=peq, k_nearest_neighbors=top_k, fields="education")
  vector_query_skills = VectorizedQuery(vector=rs, k_nearest_neighbors=top_k, fields="skills")
  vector_query_workExperience = VectorizedQuery(vector=ppe, k_nearest_neighbors=top_k, fields="workExperience")
  vector_query_education2 = VectorizedQuery(vector=mrq, k_nearest_neighbors=top_k, fields="education")
  vector_query_workExperience2 = VectorizedQuery(vector=mrq, k_nearest_neighbors=top_k, fields="workExperience")

  results = client_search_resume.search(
      search_text=None,
      vector_queries= [vector_query_summary,vector_query_education,vector_query_skills,vector_query_workExperience,vector_query_education2,vector_query_workExperience2],
      select=["docName"],
  )
  return results

def search_resumes(text, top_k, mongo_collection):
  sentences = sent_tokenize(text)
  if len(sentences)<3:
    search_results = search_resume_text_summary_embedd(text, top_k)
  else:
    search_results = serach_resume_all_embedd(text, top_k)
  results = []
  for result in search_results:
    fileName = None
    try:
      fileName = get_file_name_from_mongo(mongo_collection, result['docName'])
    except:
      continue
    results.append((fileName,convert_score_to_cosine(result['@search.score'])))
  results.sort(key = lambda x:-x[1])
  return results

def search_jds_text_summary_embedd(text, top_k):
  text_embedd = generate_embeddings(text)
  text = clean_text(text)
  vector_query_summary = VectorizedQuery(vector=text_embedd, k_nearest_neighbors=top_k, fields="summary")

  results =  client_search_jd.search(
      search_text=text,
      vector_queries= [vector_query_summary],
      select=["docName"],
  )
  return results

def serach_jds_all_embedd(text, top_k):
  gptResponse = get_chatgpt_response(prompt_begin_resume, text ,prompt_specifications_resume)

  summary = generate_embeddings(gptResponse["Summary"])
  education = generate_embeddings(combone_lists(gptResponse["Education"]))
  workex = generate_embeddings("Work Experience: "+ combone_lists(gptResponse["Work Experience"]))
  skills = generate_embeddings("Skills are: "+ combone_lists(gptResponse["Skills"]))

  vector_query_summary = VectorizedQuery(vector=summary, k_nearest_neighbors=top_k, fields="summary")
  vector_query_education = VectorizedQuery(vector=education, k_nearest_neighbors=top_k, fields="preferredEducationalQualification")
  vector_query_skills = VectorizedQuery(vector=skills, k_nearest_neighbors=top_k, fields="preferredSkills")
  vector_query_workExperience = VectorizedQuery(vector=workex, k_nearest_neighbors=top_k, fields="preferredPastExperience")

  results = client_search_jd.search(
      search_text=None,
      vector_queries= [vector_query_summary,vector_query_education,vector_query_skills,vector_query_workExperience],
      select=["docName"],
  )
  return results

def search_jds(text, top_k,mongo_collection):
  sentences = sent_tokenize(text)
  if len(sentences)<3:
    search_results = search_jds_text_summary_embedd(text, top_k)
  else:
    search_results = serach_jds_all_embedd(text, top_k)
  results = []
  for result in search_results:
    fileName = None
    try:
      fileName = get_file_name_from_mongo(mongo_collection, result['docName'])
    except:
      continue
    results.append((fileName,convert_score_to_cosine(result['@search.score'])))
  results.sort(key = lambda x:-x[1])
  return results


url_search = "https://sunflower-search.search.windows.net/"
index_name_resume = "resume-index"
index_name_jd = 'jd-index'
api_key_search = "BxtIjEICQtAWR2q5oXLJCl2dX0lGredlN9pev6q65ZAzSeCH3H3Z"
credential_search = AzureKeyCredential(api_key_search)
client_search_resume = SearchClient(endpoint=url_search, index_name=index_name_resume, credential=credential_search)
client_search_jd = SearchClient(endpoint=url_search, index_name=index_name_jd, credential=credential_search)

client_text_embedding = AzureOpenAI(
  api_key = 'f68dfd696b2a4917a892e81276af3941',
  api_version = "2024-02-01",
  azure_endpoint ='https://sunflower-openai.openai.azure.com/'
)

client_azure =  getAzureClient()

def convert_score_to_cosine(score):
  #https://learn.microsoft.com/en-us/azure/search/vector-search-ranking
  angle = 2- 1/score
  return abs(math.cos(angle))

def getResumeBestMatch(jdText, numberOfMatches):

    CONNECTION_STRING = "mongodb+srv://admin:admin123@sunflowercluster.oppjzec.mongodb.net/"
    client_mongo = MongoClient(CONNECTION_STRING)
    mongo_database = client_mongo["SunflowerDB"]
    resume_collection = mongo_database["ResumeTest"]
    results = search_resumes(jdText, numberOfMatches, resume_collection)
    return results

def getJDBestMatch(resumeText, numberOfMatches):

    CONNECTION_STRING = "mongodb+srv://admin:admin123@sunflowercluster.oppjzec.mongodb.net/"
    client_mongo = MongoClient(CONNECTION_STRING)
    mongo_database = client_mongo["SunflowerDB"]
    jd_collection = mongo_database["JDTest"]
    results = search_jds(resumeText, numberOfMatches, jd_collection)
    return results

