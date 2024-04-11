import re
from pypdf import PdfReader
from openai import OpenAI
import pandas as pd
import os

pdf_file = 'sample.pdf'
excel_file = os.path.splitext(pdf_file)[0] + '.xlsx'
reader = PdfReader(pdf_file)

num_pages = len(reader.pages)
batch_size = 5

df_combined = pd.DataFrame(columns=['Section', 'Key Information'])

for batch_start in range(0, num_pages, batch_size):
    batch_end = min(batch_start + batch_size, num_pages)
    print(batch_end)
    text = ''
    for page in reader.pages[batch_start:batch_end]:
        text += page.extract_text()
    
    message = [
        {
            "role": "system",
            "content": "You are given the text of a PDF document. Your task is to identify the section headings, paragraphs within each section, and any bullet points. For each paragraph or bullet point, output it with a prefix that indicates its location in the document structure, using the following format:\n\n<Section Number like 1.0,Subsection Number like 1.1,Sub-subsection number if have like 1.1.1,P[Paragraph Number], (Bullet Point Character if have)>. For example:<1.0,1.1,1.1.1,P[1],(a)> suggests the location of Section 1.0 Subsection 1.1 Sub-subsection 1.1.1, Paragraph 1, Bullet Point a. Similarly, for each section or subsection, output the similar prefix with its title. For example, <1.0> suggests section, <1.0,1.1> suggests subsection, <1.0,1.2,1.2.1> suggests sub-subsection with their titles. Do not modify or summarize the original text. Simply output the text with the appropriate location indicators. Moreover, you do not need to include the text outside the section."
        },
        {"role": "user", "content": text}
    ]

    client = OpenAI()
    response = client.chat.completions.create(model="gpt-4-0125-preview", messages=message)
    lines = response.choices[0].message.content
    
    lines = lines.split('\n')
    df = pd.DataFrame(columns=['Section', 'Key Information'])
    for line in lines:
        match = re.match(r'<(.+)>(.+)', line)
        if match:
            section = match.group(1)
            key_info = match.group(2).strip()
            df = pd.concat([df, pd.DataFrame({'Section': [section], 'Key Information': [key_info]})], ignore_index=True)
    
    df_combined = pd.concat([df_combined, df], ignore_index=True)

df_combined.to_excel(excel_file, index=False)