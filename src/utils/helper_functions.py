import datetime
from datetime import datetime, timedelta, date
import json
import io
from src.utils.constants import parse_command_for_args_pattern
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors

# Only keeps the articles that were published within num_days of days, default value is 1
def filter_recent_articles(articles, num_days = 1):
  # Current date and time
  current_date = datetime.now()

  # Define the timedelta for 1 day
  days_back = timedelta(days=num_days)
  filtered_articles = []
  for article in articles:
    # Convert published_parsed to datetime
    published_date = datetime(*article['published_parsed'][:6])  # Extract year, month, day, hour, min, sec

    # Check if published date is within 1 day of the current date
    if current_date - published_date <= days_back:
        filtered_articles.append(article)

  return filtered_articles

# Only return the title, link and published date of the entry
def extract_title_link_date(entry):
  title = entry['title']
  published_parsed = entry['published_parsed']
  # dt = datetime(*published_parsed[:6])
  # date = dt.strftime('%d %b %Y')
  link = entry['link']
  return {'title':title, 'published_parsed': published_parsed, 'link': link}

# Getting a list of unique entries from a list of entries
def get_unique_list(entry_list):
  unique_entries = {}
  for entry in entry_list:
    title = entry['title']
    clean_title = title.rpartition('-')[0].strip()
    if clean_title not in unique_entries:
      unique_entries[clean_title] = entry
  unique_entries_list = list(unique_entries.values())
  return unique_entries_list


def convert_timestruct_to_datestring(timestruct):
  dt = datetime(*timestruct[:6])
  datestring = dt.strftime('%d %b %Y')
  return datestring


# Functions for retrieving data, to be replaced by API calls
def get_queries_list():
    queries = []
    with open('jsonData/queries.jsonl') as f:
        for line in f:
            # Parse each line as a JSON object and add it to the list
            queries.append(json.loads(line))
        
    return queries

def get_topics():
    with open('jsonData/topics.json') as f:
        topics = json.load(f)
        
    return topics
  
# Turning a list of entries (title, link, date) into a pdf file in memory
def to_pdf_from_entries(entry_list, file_title)-> io.BytesIO:
  pdf_buffer = io.BytesIO()
  c = canvas.Canvas(pdf_buffer, pagesize=A4)
  
  width, height = A4
  c.setFont("Times-Bold", 18) 
  c.drawCentredString(width / 2, height - 1 * inch, file_title)
  
  y_pos = height - 1.5 * inch
  max_title_width = width - 2*inch
  x_pos = width / 2 - max_title_width / 2
  c.setFont("Times-Roman", 12)
  for entry in entry_list:
    title, date, link = entry["title"], entry["date"], entry["link"]

    y_pos = wrap_text(c, f"{title} ({date})", width / 2 - max_title_width / 2, y_pos, max_title_width)
    
    # Draw hyperlink text, blue colour
    c.setFillColor(colors.blue)
    c.drawString(x_pos, y_pos, "Link")
    
    # Add the underline for hyperlink text
    link_width = c.stringWidth("Link", "Times-Roman", 12)
    c.line(x_pos, y_pos - 1.2, x_pos + link_width, y_pos - 1.2)
    
    # Add hyperlink annotation
    c.linkURL(link, (x_pos, y_pos, x_pos + link_width, y_pos + 10), relative=0)
    c.setFillColor(colors.black)
    
    y_pos -= 24 # Move down a 1.7 lines
    
    if y_pos < 1 * inch:
      c.showPage()
      c.setFont("Times-Roman", 12)
      y_pos = height - 1 * inch
  
  c.showPage()
  c.save()
  
  pdf_buffer.seek(0)
  return pdf_buffer

# To wrap text in case that they are too long 
def wrap_text(c, text, x, y, max_width):
    """Function to wrap text manually based on the maximum width allowed."""
    # Create a TextObject
    text_object = c.beginText(x, y)
    text_object.setFont("Times-Roman", 12)
    # Set the width limit for the text
    lines = []
    current_line = ""
    for word in text.split():
        # Check if adding the next word exceeds the max width
        if c.stringWidth(current_line + " " + word, "Times-Roman", 12) <= max_width:
            current_line += " " + word if current_line else word
        else:
            # If it exceeds, add the current line to lines and start a new line
            lines.append(current_line)
            current_line = word
    # Add the last line
    lines.append(current_line)
    
    # Add lines to the text object
    for line in lines:
        text_object.textLine(line)
    
    # Draw the text object on the canvas
    c.drawText(text_object)
    
    # Return the new y position after drawing the text
    return y - ((len(lines)) * 14)  # Adjust spacing as needed

def get_current_date():
  today = date.today().strftime("%d-%m-%Y")
  return today

def sort_by_date(to_sort_list, order = 'desc'):
  if order == 'asc':
    list_sorted_by_date = sorted(to_sort_list, key=lambda x: x['published_parsed'])
  else:
    list_sorted_by_date = sorted(to_sort_list, key=lambda x: x['published_parsed'], reverse=True)
  
  return list_sorted_by_date

import re

def extract_flags(command_text, flags_to_extract):
    # Extract all flags and their values from the command text
    matches = {match.group('flag'): (match.group('value') or '').strip() for match in re.finditer(parse_command_for_args_pattern, command_text)}
    # print(matches)
    # Create a dictionary for the flags we want to extract, but only include those found in matches
    extracted_flags = {flag: matches[flag] for flag in flags_to_extract if flag in matches}
    
    return extracted_flags
