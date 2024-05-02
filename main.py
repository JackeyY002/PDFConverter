import re
from pypdf import PdfReader
from openai import OpenAI
import pandas as pd
import os
client = OpenAI()
#Method for solving spilt pages issue
def process_boundary_pages(text1, text2):
    boundary_message = [
        {
            "role": "system",
            "content": "You are provided with text from two consecutive pages of a PDF document. Determine if any section from the first page continues onto the second page. If so, merge the continuing section from the first page with its continuation on the second page. Return the merged section followed by '---' and then the remaining text from the second page that does not belong to the continuation. If there is no continuation, return the text from the first page followed by '---' and then all the text from the second page. Ensure there is only one '---' in your response separating the merged text and the remaining text. Last but not the least, output the specific section location at the beginning of remaining text to indicate the previous page section in case the next page did not specify. For example, previous page text --- (prvious page section: the last detailed section e.x. 2.0,2.1,P[1],(a) )"
        },
        {"role": "user", "content": f"firstPage: {text1}\n" + f"secondPage: {text2}" }
    ]
    response = client.chat.completions.create(model="gpt-4-0125-preview", messages=boundary_message)
    # print(response.choices[0].message.content)
    parts = response.choices[0].message.content.split('---')#split mark
    if len(parts) >= 2:
        merged_text = parts[0]
        remaining_text = '---'.join(parts[1:])  # Rejoin any extra parts that may have been incorrectly split
    else:
        merged_text = parts[0]
        remaining_text = "(Continue mark: no meaning)"  # Handle cases where there's no remaining text

    return merged_text.strip(), remaining_text.strip()



pdf_file = 'sample.pdf'
excel_file = os.path.splitext(pdf_file)[0] + '.xlsx'
reader = PdfReader(pdf_file)

num_pages = len(reader.pages)
batch_size = 5
last_section = None
df_combined = pd.DataFrame(columns=['Section', 'Key Information'])
next_page_text = ''
prev_page_text = ''
for batch_start in range(0, num_pages, batch_size):
    batch_end = min(batch_start + batch_size, num_pages)
    print(batch_end)
    text = ''

    if last_section: #In each analysis, passed the previous ending section number to next analysis
        text += f"(previous page section: {last_section}) "
    if not next_page_text:
        for page in reader.pages[batch_start:batch_end-1]:
            text += page.extract_text()      
    else:
        text += next_page_text
        for page in reader.pages[batch_start+1:batch_end-1]:
            text += page.extract_text()
    prev_page_text = reader.pages[batch_end-1].extract_text()
    if batch_end < num_pages:
        next_page_text = reader.pages[batch_end].extract_text()
    else:
        next_page_text = ''
    # print(prev_page_text + '\n*******\n' + next_page_text)
    merged_text, remaining_text = process_boundary_pages(prev_page_text, next_page_text)
    text += merged_text
    next_page_text = remaining_text
    message = [
        {
            "role": "system",
            "content": "You are given the text of a PDF document. Your task is to identify the section headings, paragraphs within each section, and any bullet points. For each paragraph or bullet point, output it with a prefix that indicates its location in the document structure, using the following format:\n\n<Section Number like 1.0,Subsection Number like 1.1,Sub-subsection number if have like 1.1.1,P[Paragraph Number], (Bullet Point Character if have),(Extra Bullet Point Character if have)>. For example:<1.0,1.1,1.1.1,P[1],(a),(1)> suggests the location of Section 1.0 Subsection 1.1 Sub-subsection 1.1.1, Paragraph 1, Bullet Point a, extra bullet point. Similarly, for each section or subsection, output the similar prefix with its title. For example, <1.0> suggests section, <1.0,1.1> suggests subsection, <1.0,1.2,1.2.1> suggests sub-subsection with their titles. Do not modify or summarize the original text. Simply output the text with the appropriate location indicators. Moreover, you do not need to include the text outside the section. While encounter Appendix, treat it like a normal big section number, a example could be Appendix A, followed by some subsection number, P[],bullet points. At the beginning of each text, l will provide the previous end section number for you to refer if the text did not specify."
        },
        {"role": "user", "content": text}
    ]

    
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
    if not df.empty:
        last_section = df['Section'].iloc[-1]
        print('Last section extracted:', last_section)
    else:
        last_section = None
        print('No sections found in this batch')
df_combined.to_excel(excel_file, index=False)

