import re
from pypdf import PdfReader
from openai import OpenAI
import pandas as pd
reader = PdfReader('example.pdf')


text = ''
for page in reader.pages:
    text += page.extract_text()
print(text)
print("*************************")
message = [
    {
        "role": "system",
        "content": "You are given the text of a PDF document. Your task is to identify the section headings, paragraphs within each section, and any bullet points. For each paragraph or bullet point, output it with a prefix that indicates its location in the document structure, using the following format:\n\n<Section Number like 1.0,Subsection Number like 1.1,Sub-subsection number if have like 1.1.1,P[Paragraph Number], (Bullet Point Character if have)>. For example:<1.0,1.1,1.1.1,P[1],(a)> suggests the location of Section 1.0 Subsection 1.1 Sub-subsection 1.1.1, Paragraph 1, Bullet Point a. Similarily, for each section or subsection, output the similar prefix with its title. For example, <1.0> suggest section, <1.0,1.1> suggests subsection, <1.0,1.2,1.2.1> suggest sub-subsection with their titles. Do not modify or summarize the original text. Simply output the text with the appropriate location indicators. Moreover, you do not need to include the text outside the section. "
    },
    {"role": "user", "content": text}
]

client = OpenAI()
response = client.chat.completions.create(model="gpt-4-0125-preview", messages=message)
lines = response.choices[0].message.content
print(response.choices[0].message.content)

# split the lines and extract each section with its key-info
lines = lines.split('\n')
df = pd.DataFrame(columns=['Section', 'Key Information'])
for line in lines:
    match = re.match(r'<(.+)>(.+)', line)
    if match:
        section = match.group(1)
        key_info = match.group(2).strip()
        df = pd.concat([df, pd.DataFrame({'Section': [section], 'Key Information': [key_info]})], ignore_index=True)

df.to_excel('example.xlsx', index=False)



