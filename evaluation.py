import datetime
from dotenv import load_dotenv, find_dotenv
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import CSVLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.evaluation.qa import QAGenerateChain
#import langchain
#langchain.debug = True

# Load environment variables
_ = load_dotenv(find_dotenv())

# Account for deprecation of LLM model
current_date = datetime.datetime.now().date()
target_date = datetime.date(2024, 6, 12)

# Set the model variable based on the current date
llm_model = "gpt-3.5-turbo" if current_date > target_date else "gpt-3.5-turbo-0301"

# File and data loading
file = 'llm_memory.csv'
loader = CSVLoader(file_path=file)
data = loader.load()

index = VectorstoreIndexCreator(
    vectorstore_cls=DocArrayInMemorySearch
).from_loaders([loader])

llm = ChatOpenAI(temperature=0.0, model=llm_model)
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=index.vectorstore.as_retriever(),
    verbose=True,
    chain_type_kwargs={
        "document_separator": "history"
    }
)
print(f'data[189]:\n{data[0]}\n')
print(f'data[190]:\n{data[1]}\n')

example_gen_chain = QAGenerateChain.from_llm(ChatOpenAI(model=llm_model))
new_examples = example_gen_chain.apply_and_parse(
    [{"doc": t} for t in data[:1]]
)
print(f'new_examples[0]:\n{new_examples[0]}\n')
print(f'data[0]:\n{data}\n')

embeddings = OpenAIEmbeddings()
embed = embeddings.embed_query(f"{data[1]}")
print(f'embed:\n{len(embed)}\n')
print(f'embed[:5]\n{embed[:5]}\n')
