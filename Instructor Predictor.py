from tkinter import *
import docclass
import urllib2
from bs4 import BeautifulSoup


class PI_Estimator(Frame):
    def __init__(self, parent):  # Initializing the UI
        Frame.__init__(self)
        self.initUI()
        self.my_predictor = Predictor()  # creating predictor object

    def initUI(self):  # Creates the UI
        self.label_title = Label(text="PI Estimator Tool for SEHIR CS Projects", font=("", "20", "bold"), fg="white", bg="teal").pack(fill=X)
        self.entry_url_people = Entry(width=100, justify=CENTER)
        self.entry_url_people.pack(pady=(20, 10))
        self.entry_url_people.insert(0, "http://cs.sehir.edu.tr/en/people/")
        self.entry_url_research = Entry(width=100, justify=CENTER)
        self.entry_url_research.pack(pady=(0, 10))
        self.entry_url_research.insert(0, "http://cs.sehir.edu.tr/en/research/")
        self.button_fetch = Button(text="Fetch", width=10, command=self.fetch_data)
        self.button_fetch.pack(padx=10, pady=10)
        self.frame_main = Frame()
        self.frame_main.pack()
        self.label_projcets = Label(self.frame_main, text="Projects", font=("", "10", "bold")).grid(row=0, column=0)
        self.frame_listbox = Frame(self.frame_main)
        self.frame_listbox.grid(row=1, column=0)
        self.scrollbar_proteins = Scrollbar(self.frame_listbox)
        self.scrollbar_proteins.pack(side=RIGHT, fill=Y)
        self.listbox = Listbox(self.frame_listbox, yscrollcommand=self.scrollbar_proteins.set, height=10, width=90)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.pack(side=LEFT)
        self.scrollbar_proteins.configure(command=self.listbox.yview)
        self.label_prediction_title = Label(self.frame_main, text="Prediction", font=("", "10", "bold")).grid(row=0, column=1)
        self.label_prediction_placeholder = Label(self.frame_main, width=15, height=1, text="", font=("", "15", "bold"))
        self.label_prediction_placeholder.grid(row=1, column=1, padx=(20, 0))
        self.pack(fill=BOTH)

    def fetch_data(self):  # calls methods from predictor class to fetch the necessary data from the provided links and trains the classifier
        self.my_predictor.fetch_publications()  # gets the publications
        self.my_predictor.fetch_projects()  # gets the research projects
        insertion_list = []
        for project in self.my_predictor.projects:
            insertion_list.append(project)
        insertion_list.sort()  # for alphabetical order
        self.my_predictor.train_classifier()  # calls the method from predictor class to create and train the naive bayes classifier
        for item in insertion_list:
            self.listbox.insert(END, item)

    def on_select(self, event):  # calls the method from predictor class to make a PI prediction for selected project
        self.my_predictor.predict_PI()


class Predictor:  # Predictor class for collecting data, training and creating classifier and make prediction
    def __init__(self):
        self.classifier = ""
        self.faculty_members = {}
        self.projects = {}

    def fetch_members(self):  # collects the links to the members profile pages from the first link
        url = app.entry_url_people.get()
        page = urllib2.urlopen(url)
        doc = page.read()
        soup = BeautifulSoup(doc, 'html.parser')
        items = soup.find_all(class_="member")
        links_temp = []
        for i in items:
            for tag in i.find_all('a'):
                links_temp.append(tag.get('href'))
        links = []
        i = 0
        while i < len(links_temp):
            links.append("http://cs.sehir.edu.tr"+links_temp[i])
            i += 3
        return links

    def fetch_publications(self):  # goes to each members profile page and collects all the necessary data
        list_of_members_url = self.fetch_members()
        for member_url in list_of_members_url:
            url = member_url
            page = urllib2.urlopen(url)
            doc = page.read()
            soup = BeautifulSoup(doc, 'html.parser')
            name = soup.find_all('h3')
            name = name[0].text.split()
            name = name[0] + " " + name[-1]
            table = soup.find_all(class_="tab-pane active pubs")
            publications = []
            for item in table:
                for tag in item.find_all("li"):
                    app_item = tag.text.strip()[4:]  # filtering out unwanted info and characters
                    while app_item.startswith('\n'):
                        app_item = app_item[1:]
                    if app_item.endswith("[1\n  Citation]"):
                        app_item = app_item[:-19]
                    elif app_item.endswith("\n  \n  Citations]"):
                        app_item = app_item[:-23]
                        while app_item.endswith('\n'):
                            app_item = app_item[:-1]
                        app_item = app_item
                    publications.append(app_item)
            current_fac_member = FacultyMember(name, member_url, publications)  # crating a faculty member object for adding to database
            self.faculty_members.setdefault(name, current_fac_member)  # adding each member to the database

    def fetch_projects(self):  # goes to the projects page from the second link and gets all the wanted info
        url = app.entry_url_research.get()
        page = urllib2.urlopen(url)
        doc = page.read()
        soup = BeautifulSoup(doc, 'html.parser')
        items = soup.find_all(class_="list-group-item")
        for item in items:
            title = item.find_all("h4")
            title = title[0].text.strip()
            PI = item.find_all("p")
            PI = PI[2].find("a")
            PI = PI.text.strip()
            summary = item.find(class_="gap")
            summary = summary.text
            current_r_pro = ResearchProject(title, summary, PI)  # crates a research project object for adding into databse
            if PI not in self.faculty_members:
                continue
            else:
                self.projects.setdefault(title, current_r_pro)  # adding each project to the database

    def train_classifier(self):  # crates and trains a naive bayes classifier object
        self.classifier = docclass.naivebayes(docclass.getwords)
        for member in self.faculty_members:  # training the naive bayes classifier object with the publications of each member
            for publication in self.faculty_members[member].publications:
                self.classifier.train(publication, member)

    def predict_PI(self):  # makes a PI prediction for the selected project
        selection = app.listbox.get(app.listbox.curselection())  # gets the selection
        project_summary = self.projects[selection].summary
        data = selection + " " + project_summary
        prediction = self.classifier.classify(data)  # calls a method from classifier class from docclass.py to make a prediciton
        app.label_prediction_placeholder.configure(text=prediction)
        if prediction == self.projects[selection].PI_name:  # configures the background of the label based on the correctness of the prediction
            app.label_prediction_placeholder.configure(bg="green")
        else:
            app.label_prediction_placeholder.configure(bg="red")


class FacultyMember:  # class for a faculty member
    def __init__(self, name, profile_url, publications):
        self.name = name
        self.profile_url = profile_url
        self.publications = publications


class ResearchProject:  # class for a research project
    def __init__(self, title, summary, PI_name):
        self.title = title
        self.summary = summary
        self.PI_name = PI_name


root = Tk()
root.geometry("1050x500")
root.title("PI Estimator Tool for SEHIR CS Projects")
app = PI_Estimator(root)
root.mainloop()
