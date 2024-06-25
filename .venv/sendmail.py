import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from pathlib import Path

current_dir = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
envars = current_dir / ".env"
load_dotenv(envars)

sender_email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")

current_time = datetime.now()  # gets current date and time
date = current_time.strftime("%Y/%m/%d")  # date in yyyy/mm/dd format
date2=current_time.strftime("%Y-%m-%d")

websites= []
websites.append("https://www.nytimes.com/")  #adds nyt to website list
websites.append("https://www.washingtonpost.com/")  #adds wapo to website list
websites.append("https://www.reuters.com/")
links = []  # list of links to articles to add to email
titles = []  # list of corresponding article titles to add to email
keywords = []  # keywords in links
flag = 0  # flag for if link contains existing keyword
linknum = 3  # number of links to add from each website
appendcounter = 0  # number of links added from each website
reuterstitles = []



def getdata():
 global links, titles, keywords, appendcounter, linknum, flag, date, date2, websites, reuterstitles
 driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
 for website in websites:

     if ("reuters" in website):
       driver.get(website)
       soup = BeautifulSoup(driver.page_source, 'lxml')
     else:
      results = requests.get(website)  # sends requests
      soup = BeautifulSoup(results.content, 'lxml')

     for link in soup.find_all("a", href=True):  # finds all hyperlinks that redirect
        linko = str(link.get('href'))  # gets the link

        if (date in linko or date2 in linko) and linko not in links:  # checks that article is from today and isn't a duplicate
            for keyword in keywords:  # checks if link contains any keywords from other links
                if keyword in linko:  # if so, doesn't add it to the list
                    flag += 1
            if flag == 0:  # if it contains no existing keywords, add it to the list and store keywords
                if (website == "https://www.reuters.com/"):
                    linko = "https://www.reuters.com" + linko
                    reuterstitles.append(link.find('span').text)
                links.append(linko)
                appendcounter += 1
                if website=="https://www.washingtonpost.com/" or website=="https://www.reuters.com/": #obatining keywords based on link structure
                    linko=linko[:-1]
                linko = linko.split('/')
                linko = linko[-1]
                if ".html" in linko:
                    linko = linko[:-5]
                linko = linko.split("-")
                for word in linko:
                    if len(word)>4:
                        keywords.append(word)
            flag = 0
        if appendcounter == linknum:  # once desired number of links have been found, finish
            appendcounter = 0
            keywords=[]
            break

 for link in links:
    if links.index(link)<(linknum*2):
      if "nytimes" in link:
       driver.get(link)
       souptwo=BeautifulSoup(driver.page_source, 'lxml')
      else:
          resulto = requests.get(link)
          souptwo = BeautifulSoup(resulto.content,'lxml')
      title = souptwo.find("h1")
      span = title.find("span")
      if span is not None:
          title = span.text
          titles.append(title)
      else:
          title=title.text
          titles.append(title)
 for roo in reuterstitles:
   titles.append(roo)
 driver.close()

def sendmail(receiver):
 global linknum, links, titles, sender_email, password, current_time
 date3 = current_time.strftime("%m/%d/%Y")
 msg = EmailMessage()
 msg['Subject'] = "Today's Top Stories " + date3
 msg['From'] = formataddr(("Zane's Newsletter", f'{sender_email}'))
 msg['To'] = receiver
 message = "\nHere are today's breaking headlines, courtesy of Zane's Program: \n\n"
 message += "First, here's the top " + str(linknum) + " stories from the New York Times:\n\n"
 for numbo, link in enumerate(links):
     if numbo == 3:
         message += "\nNext, check out the top " + str(linknum) + (" stories from The Washington Post:\n")
     if numbo == 6:
         message += "\nFinally, here are the top " + str(linknum) + " articles from Reuters:\n"
     message += titles[numbo]
     message += ": \n"
     message += link
     message += '\n'

 msg.set_content(message)
 msg.add_alternative(

   f"""\
    <html>
      <h3> Here are today's breaking headlines, courtesy of Zane's Program:</h3>
        <body> 
           <p> <strong> First, here's the top {linknum} stories from the New York Times: </strong> </p>
           <p> {titles[0]}: </p>
           <p> {links[0]} </p>
           <p> {titles[1]}: </p>
           <p> {links[1]} </p>   
           <p> {titles[2]}: </p>
           <p> {links[2]} </p>
           <p> <strong> Next, check out the top {linknum} stories from The Washington Post: </strong> </p>   
           <p> {titles[3]}: </p>
           <p> {links[3]} </p>   
           <p> {titles[4]}: </p> 
           <p> {links[4]} </p>  
           <p> {titles[5]}: </p>  
           <p> {links[5]} </p> 
           <p> <strong> Finally, here are the top {linknum} articles from Reuters: </strong> </p>
           <p> {titles[6]}: </p>
           <p> {links[6]} </p>   
           <p> {titles[7]}: </p>  
           <p> {links[7]} </p> 
           <p> {titles[8]}: </p> 
           <p> {links[8]} </p>
           <p> Enjoy reading! </p>
      </body>
    </html>      
    """,
     subtype="html",
   )
 server = smtplib.SMTP('smtp.gmail.com', 587)
 server.starttls()
 server.login(sender_email, password)
 print(msg)
 print(message)
 server.sendmail(sender_email, receiver, msg.as_string())



# adding email to mailing list prompt
email_to_add= input("Enter an email to add to the mailing list (if you want):")
if email_to_add != "":
  mailinglist = open("receivers.txt", "a")
  mailinglist.write(email_to_add + "\n")
  print(email_to_add + " has been added to the mailing list! \n")

# removing email from mailing list prompt
email_to_remove= input("Enter an email to remove from the mailing (up to you ofc):")
if email_to_remove != "":
    mailinglist = open("receivers.txt", "r")
    receiverslist = mailinglist.readlines()
    mailinglist= open("receivers.txt", "w")
    for email in receiverslist:
        if email.strip('\n') != email_to_remove:
            mailinglist.write(email)
    print("email removed! (if it was there)")

yesorno= input("Do you want to send the newsletter? (Y/N):")
if yesorno == "Y" or yesorno == "y":
    totalmail = 0
    getdata()
    listo = open("receivers.txt", "r")
    listlist = listo.readlines()
    for line in listlist:
        sendmail(str(line.strip("\n")))
        totalmail +=1
    print (totalmail + " emails sent!")


