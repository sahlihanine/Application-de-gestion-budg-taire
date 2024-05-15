from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.properties import BooleanProperty
from kivy.clock import Clock
from kivy.animation import Animation
from datetime import datetime
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.core.audio import SoundLoader
from kivy.properties import StringProperty
import sqlite3
import calendar
import hashlib
import re


#######################################################################################################################
class Database:
    def __init__(self, db_name='user_data.db'):
        self.conn = sqlite3.connect(db_name)
        self.c = self.conn.cursor()
        self.create_table()  # Crée la table des utilisateurs lors de l'initialisation

    def create_table(self):

        ##############################################################################
        ######### Table de base des coordonnées des utilisateur #########
        ##############################################################################
        self.c.execute('''CREATE TABLE IF NOT EXISTS users
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT, salaire REAL, dépencesfixes REAL,password TEXT )
                          ''')
        ########################################################################################
        ######### Table de base de repartition de budget des utilisateur ##########
        ########################################################################################
        self.c.execute('''CREATE TABLE IF NOT EXISTS dépenses_utilisateur
                          (user_id INTEGER, dépences_primaires REAL , dépences_secondaires REAL, investissement REAL,
                          FOREIGN KEY(user_id) REFERENCES users(id))
                          ''')
        ########################################################################################
        ######### Table de base de feedback des utilisateur ##########
        ########################################################################################
        self.c.execute('''CREATE TABLE IF NOT EXISTS feedback
                          (user_id INTEGER, feedback_text TEXT, FOREIGN KEY(user_id) REFERENCES users(id))
                          ''')
        self.conn.commit()
        ########################################################################################
        ########Table de base des transactions des utilisateur##################################
        ########################################################################################
        self.c.execute('''CREATE TABLE IF NOT EXISTS transactions
                          (user_id INTEGER, type_depences TEXT, catégorie TEXT, montant REAL, transaction_date DATETIME,  FOREIGN KEY(user_id) REFERENCES users(id))
                          ''')
        self.conn.commit()
        ########################################################################################




##############################################################################
######### Fonctions de base des coordonnées des utilisateur #########
##############################################################################
    def validate_password(self, password):
        return len(password) >= 6  and re.search("[a-z]", password) and re.search("[A-Z]", password)

    def is_valid_email(self, email):
        pattern = r'^[\w\.-]+@[\w\.-]+$'
        return re.match(pattern, email)

    def get_user_id(self, email):
        self.c.execute("SELECT id FROM users WHERE email=?", (email,))
        user_id = self.c.fetchone()
        if user_id:
            return user_id[0]
        else:
            return None

    def create_user_and_get_id(self, username, email, salaire,dépencesfixes, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.c.execute("INSERT INTO users (username, email,  salaire, dépencesfixes, password) VALUES (?, ?, ?, ?, ?)",
                       (username, email, salaire, dépencesfixes ,hashed_password))
        self.conn.commit()
        return self.get_user_id(email)


    def email_exists(self, email):
        self.c.execute("SELECT * FROM users WHERE email=?", (email,))
        if self.c.fetchone():
            return True
        else:
            return False

    def user_exists(self, username):
        self.c.execute("SELECT * FROM users WHERE username=?", (username,))
        if self.c.fetchone():
            return True
        else:
            return False

    def get_user(self, email, password):
        self.c.execute("SELECT password FROM users WHERE email=?", (email,))
        stored_password = self.c.fetchone()
        if stored_password:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if stored_password[0] == hashed_password:
                return True  # Utilisateur trouvé et mot de passe correct
            else:
                return False  # Mot de passe incorrect
        else:
            return None  # Email introuvable

    def get_user_info_by_id(self, user_id):
        self.c.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user_info = self.c.fetchone()
        if user_info:
            return {'username': user_info[1], 'email': user_info[2],'salaire': user_info[3],'dépencesfixes': user_info[4]}
        else:
            return None

    def update_user_info(self, user_id, username, email, salaire, dépencesfixes, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.c.execute("UPDATE users SET username=?, email=?, salaire=?, dépencesfixes=?, password=? WHERE id=?",
                       (username, email, salaire, dépencesfixes, hashed_password, user_id))
        self.conn.commit()

    def update_user_info_without_password(self, user_id, username, email, salaire, dépencesfixes):
        self.c.execute("UPDATE users SET username=?, email=?, salaire=?, dépencesfixes=? WHERE id=?",
                       (username, email, salaire, dépencesfixes, user_id))
        self.conn.commit()



########################################################################################
######### Fonctions de base de repartition de budget des utilisateur ###################
########################################################################################

    def create_user_expenses(self, user_id, dépences_primaires, dépences_secondaires, investissement):
        self.c.execute("INSERT INTO dépenses_utilisateur (user_id, dépences_primaires, dépences_secondaires, investissement) VALUES (?, ?, ?, ?)",
                       (user_id,dépences_primaires, dépences_secondaires, investissement))
        self.conn.commit()


    def update_user_expenses(self, user_id, dépences_primaires, dépences_secondaires, investissement):
        self.c.execute("UPDATE dépenses_utilisateur SET dépences_primaires=?, dépences_secondaires=?, investissement=? WHERE user_id=?",
                       (dépences_primaires, dépences_secondaires, investissement, user_id))
        self.conn.commit()

    def calculate_budget_allocation(self, salaire, dépencesfixes):
        user_id = App.get_running_app().user_id  # Récupérer l'user_id de l'application
        if user_id:
            db_instance = App.get_running_app().db
            user_info = db_instance.get_user_info_by_id(user_id)
            if user_info:
                salaire_brut = salaire - dépencesfixes
                dépences_primaires = salaire_brut * 0.5
                dépences_secondaires = salaire_brut * 0.3
                investissement = salaire_brut * 0.2
                db_instance.create_user_expenses(user_id,dépences_primaires, dépences_secondaires, investissement)
                return dépences_primaires, dépences_secondaires, investissement

    def update_user_info_money(self, user_id, salaire, dépencesfixes):
        self.c.execute("UPDATE users SET salaire=?, dépencesfixes=? WHERE id=?",
                       (salaire, dépencesfixes, user_id))
        self.conn.commit()

    def get_user_expenses(self, user_id):
        self.c.execute("SELECT dépences_primaires, dépences_secondaires, investissement FROM dépenses_utilisateur WHERE user_id=?",
                       (user_id,))
        expenses = self.c.fetchone()
        if expenses:
            return expenses
        else:
            return None

########################################################################################
######### Fonctions de base de feedback des utilisateur ################################
########################################################################################
    def save_feedback(self, user_id, feedback):
        self.c.execute("INSERT INTO feedback (user_id, feedback_text) VALUES (?, ?)",
                       (user_id, feedback))
        self.conn.commit()


########################################################################################
###################Fonction de depences courantes et transaction########################
########################################################################################
    def record_transaction(self, user_id, type_depences, categorie, montant, transaction_date):
        self.c.execute("INSERT INTO transactions (user_id, type_depences , catégorie, montant, transaction_date) VALUES (?, ?, ?, ?, ?)",
                       (user_id, type_depences, categorie, montant, transaction_date))
        self.conn.commit()

    def allocate_expenses(self, user_id, montant):
        # Récupérer les dépenses actuelles de l'utilisateur
        dépences_primaires, dépences_secondaires, investissement = self.get_user_expenses(user_id)

        # Mettre à jour les dépenses en fonction de la catégorie
        dépences_primaires -= montant

        # Mettre à jour les dépenses dans la base de données
        self.c.execute(
            "UPDATE dépenses_utilisateur SET dépences_primaires=?, dépences_secondaires=?, investissement=? WHERE user_id=?",
            (dépences_primaires, dépences_secondaires, investissement, user_id))
        self.conn.commit()

    def subtract_from_savings(self, user_id, montant):
        # Récupérer l'épargne actuelle de l'utilisateur
        dépences_primaires, dépences_secondaires, investissement = self.get_user_expenses(user_id)

        # Soustraire le montant de l'épargne
        dépences_secondaires -= montant

        # Mettre à jour l'épargne dans la base de données
        self.c.execute(
            "UPDATE dépenses_utilisateur SET dépences_primaires=?, dépences_secondaires=?, investissement=? WHERE user_id=?",
            (dépences_primaires, dépences_secondaires, investissement, user_id))
        self.conn.commit()

    def get_user_transactions(self, user_id):
        self.c.execute("SELECT type_depences, catégorie, montant, transaction_date FROM transactions WHERE user_id=?", (user_id,))
        transactions = self.c.fetchall()
        return transactions


#####################################################################################################################
##############################################classes et fonctions ##################################################
#####################################################################################################################



######introduction######
class IntroductionScreen(Screen):
    def __init__(self, **kwargs):
        super(IntroductionScreen, self).__init__(**kwargs)
        Clock.schedule_once(self.switch_to_home, 5)
        self.start_animation()

    def switch_to_home(self, dt):
        self.manager.current = 'Home'  # Passer à la page d'accueil

    def start_animation(self):
        image_widget = self.ids.my_image_id
        anim = Animation(size=(350, 350), duration=2)
        anim.start(image_widget)

######Inscription######
class Incriptionscreen(Screen):
    def toggle_password_visibility(self):
        password_input = self.ids.password_input
        password_input.password = not password_input.password

    def __init__(self, **kwargs):
        super(Incriptionscreen, self).__init__(**kwargs)
        self.db = Database()
        self.db.create_table()

    def save_data(self, username, email, salaire, dépencesfixes,password):
        # Vérifie si l'utilisateur existe déjà dans la base de données
        if self.db.user_exists(username):
            self.ids.error_label.text = "Nom d'utilisateur déjà utilisé!"
            self.ids.username_input.text = ""
            return

        # Vérifie si l'adresse e-mail est valide
        if not self.db.is_valid_email(email):
            self.ids.error_label.text = "Adresse e-mail invalide"
            self.ids.email_input.text = ""
            return

        # Vérifie si l'adresse e-mail existe déjà
        if self.db.email_exists(email):
            self.ids.error_label.text = "L'adresse mail existe déjà!"
            self.ids.email_input.text = ""
            return

        # Vérifie si le mot de passe est valide
        if not self.db.validate_password(password):
            self.ids.error_label.text = "Mot de passe invalide(doit contenir des lettres majiscule,\n miniscule et des chiffres de longeur>=6)"
            self.ids.password_input.text = ""
            return

        # Enregistrement des données dans la base de données
        user_id = self.db.create_user_and_get_id(username, email, salaire, dépencesfixes, password)
        App.get_running_app().user_id = user_id  # Enregistrez l'user_id dans l'application
        # Passer à l'écran "SalaireDépencesFixes"
        self.manager.current = 'SalaireDépencesFixes'
        #Effacer le label d'erreur
        self.ids.error_label.text = ""
        # Effacer les champs de saisie après l'inscription réussie
        self.ids.username_input.text = ""
        self.ids.email_input.text = ""
        self.ids.password_input.text = ""


    def on_save(self):
        username = self.ids.username_input.text
        email = self.ids.email_input.text
        password = self.ids.password_input.text
        if username=="" and email=="" and password=="":
            self.ids.error_label.text = "Les champs sont vides!"
            return
        if username=="":
            self.ids.error_label.text = "Champ de nom d'utilisateur vide!"
            return
        if email=="":
            self.ids.error_label.text = "Champ de email vide!"
            return
        if password=="":
            self.ids.error_label.text = "Champ mot de passe vide!"
            return
        salaire=0.0
        dépencesfixes=0.0
        self.save_data(username, email, salaire, dépencesfixes,password)



######Connection######
class ConnectionScreen(Screen):

    def toggle_password_visibility(self):
        password_input = self.ids.password_input
        password_input.password = not password_input.password

    def __init__(self, **kwargs):
        super(ConnectionScreen, self).__init__(**kwargs)
        self.db = Database()

    def on_login(self):
        self.ids.error_label.text = ""  # Effacer le message d'erreur précédent
        email = self.ids.email_input.text
        password = self.ids.password_input.text
        if not all((email, password)):
            self.ids.error_label.text = "Veuillez remplir tous les champs!"
            return
        if email=="":
            self.ids.error_label.text = "Champ de email vide!"
            return
        if password=="":
            self.ids.error_label.text = "Champ mot de passe vide!"
            return
        result = self.db.get_user(email, password)
        if result is True:
            user_id = App.get_running_app().db.get_user_id(email)
            App.get_running_app().user_id = user_id  # Enregistrez l'user_id dans l'application
            self.manager.get_screen('Profil').load_user_info(user_id)
            user_info = App.get_running_app().db.get_user_info_by_id(user_id)
            if user_info['salaire'] == 0 or user_info['dépencesfixes'] == 0:
                # Rediriger vers la page "SalaireDépensesFixes" si le salaire ou les dépenses fixes sont égaux à 0
                self.manager.current = 'SalaireDépencesFixes'
                self.ids.error_label.text = ""
            else:
                self.manager.current = 'Menu'
                self.ids.error_label.text = ""
        elif result is False:
            self.ids.error_label.text = "Mot de passe incorrect"
            self.ids.password_input.text = ""
            return
        elif result is None:
            self.ids.error_label.text = "Adresse e-mail introuvable"
            self.ids.email_input.text = ""
            return
        # Effacer les champs de saisie après la connexion réussie
        self.ids.email_input.text = ""
        self.ids.password_input.text = ""



class Homescreen(Screen):
    pass


class MenuScreen(Screen):
    def hide_buttons(self):
        settings_button = self.ids.settings_button
        calendar_button = self.ids.calendar_button
        help_button = self.ids.help_button

        # Set the opacity of each button to 0
        settings_button.opacity = 0
        calendar_button.opacity = 0
        help_button.opacity = 0

    def reveal_buttons(self):
        settings_button = self.ids.settings_button
        calendar_button = self.ids.calendar_button
        help_button = self.ids.help_button

        settings_button.opacity = 1
        calendar_button.opacity = 1
        help_button.opacity = 1





######Parametre######
class SettingsScreen(Screen):
    dark_mode = BooleanProperty(False)  # Propriété pour suivre l'état du mode sombre
    sound_enabled = BooleanProperty(True)  # Propriété pour suivre l'état du son
    sound = SoundLoader.load('son.wav')

    def reveal_menu_buttons(self):
        # Obtenir le gestionnaire d'écrans
        screen_manager = self.manager

        # Obtenir la référence à MenuScreen
        menu_screen = screen_manager.get_screen('Menu')

        # Appeler la méthode pour révéler les boutons du menu
        menu_screen.reveal_buttons()

    def toggle_dark_mode(self, value):
        self.dark_mode = value
        if self.dark_mode:
            Window.clearcolor = (0, 0, 0, 1)
            # Couleur de fond noire
        else:
            Window.clearcolor = (1, 1, 1, 1)
            # Couleur de fond blanche

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        return

    def play_sound(self):
        if self.sound_enabled and self.sound:
            self.sound.play()
        return


######salaire et depences fixes######
class SalaireDépencesFixesScreen(Screen):
    def save_data(self):
        # Récupérer les valeurs saisies dans les champs
        salaire_input = self.ids.salaire_input
        dépences_fixes_input = self.ids.dépences_fixes_input

        salaire_text = salaire_input.text.strip()
        dépences_fixes_text = dépences_fixes_input.text.strip()

        # Vérifier si les valeurs sont valides
        if not salaire_input or not dépences_fixes_input:
            # Afficher un message d'erreur si les champs sont vides
            self.ids.error_label.text = "Veuillez remplir tous les champs."
            return
        try:
            # Convertir les valeurs en float
            salaire = float(salaire_text)
            dépencesfixes = float(dépences_fixes_text)
        except ValueError:
            # Afficher un message d'erreur si les valeurs ne peuvent pas être converties en float
            self.ids.error_label.text = "Les valeurs doivent être des chiffres."
            self.ids.salaire_input.text = ""
            self.ids.dépences_fixes_input.text = ""
            return

        if salaire == 0 :
            self.ids.error_label.text = "Le salaire e ne peut pas être égal à zéro."
            self.ids.salaire_input.text = ""
            return
        if dépencesfixes == 0:
            self.ids.error_label.text = "Les dépencesfixes  ne peuvent pas être égaux à zéro."
            self.ids.dépences_fixes_input.text = ""
            return
        if dépencesfixes>salaire:
            self.ids.error_label.text = "Les dépencesfixes  ne peuvent pas être supérieures au salaire!"
            self.ids.dépences_fixes_input.text = ""
            return
        if dépencesfixes==salaire:
            self.ids.error_label.text = "Les dépencesfixes  ne peuvent pas être égaux au salaire!"
            self.ids.dépences_fixes_input.text = ""
            return
        user_id = App.get_running_app().user_id  # Récupérer l'user_id de l'application
        if user_id:
            # Mettre à jour les informations de l'utilisateur dans la base de données
            App.get_running_app().db.update_user_info_money(user_id, salaire, dépencesfixes)
            self.manager.get_screen('Profil').load_user_info(user_id)
            App.get_running_app().db.calculate_budget_allocation(salaire,dépencesfixes)
            # Passer à l'écran "SalaireDépencesFixes"
            self.manager.current = 'Menu'
            self.ids.salaire_input.text = ""
            self.ids.dépences_fixes_input.text = ""
        self.ids.error_label.text = ""


######repartition de budget######
class RépartitionBudgétaireScreen(Screen):
    def calculate_and_update_budget_allocation(self):
        user_id = App.get_running_app().user_id  # Récupérer l'user_id de l'application
        db_instance = App.get_running_app().db
        user_expenses = db_instance.get_user_expenses(user_id)
        if user_expenses:
            dépences_primaires, dépences_secondaires, investissement = user_expenses
            # Mise à jour des éléments de l'interface utilisateur
            self.ids.dépences_primaires_value_label.text = str(dépences_primaires)+str(" dt")
            self.ids.dépences_secondaires_value_label.text = str(dépences_secondaires)+str(" dt")
            self.ids.Investissement_value_label.text = str(investissement)+str(" dt")


######feedback######
class FeedbackScreen(Screen):
    def submit_feedback(self):
        feedback = self.ids.feedback_input.text
        if feedback=="":
            self.ids.error_label.text = "votre message est vide!"
            return
        else:
            user_id = App.get_running_app().user_id
            if user_id:
                App.get_running_app().db.save_feedback(user_id, feedback)
                #self.send_feedback_email(user_id, feedback)
                self.ids.feedback_input.text = ""  # Efface le champ de saisie après soumission
                self.ids.error_label.text = "votre message est envoyer avec succé"



######Profil######
class ProfilScreen(Screen):
    def toggle_password_visibility(self):
        password_input = self.ids.password_input
        password_input.password = not password_input.password
    def load_user_info(self, user_id):
        db_instance = App.get_running_app().db
        user_info = db_instance.get_user_info_by_id(user_id)
        if user_info:
            self.ids.username_input.text = user_info['username']
            self.ids.email_input.text = user_info['email']
            self.ids.salaire_input.text = str(user_info['salaire'])
            self.ids.dépences_fixes_input.text = str(user_info['dépencesfixes'])

    def save_changes(self):
        db_instance = App.get_running_app().db
        user_id = App.get_running_app().user_id  # Récupérer l'user_id de l'application
        user_expenses = db_instance.get_user_expenses(user_id)
        if user_expenses:
            dépences_primaires, dépences_secondaires, investissement = user_expenses
        if user_id:
            user_info = db_instance.get_user_info_by_id(user_id)
            if user_info:
                previous_username = user_info['username']
                previous_email = user_info['email']
                previous_salaire=user_info['salaire']
                previous_dépencesfixes=user_info['dépencesfixes']
            username = self.ids.username_input.text
            email = self.ids.email_input.text
            password = self.ids.password_input.text
            salaire = float(self.ids.salaire_input.text)
            dépencesfixes=float(self.ids.dépences_fixes_input.text)
            if username != previous_username:
                # Vérifie si l'utilisateur existe déjà dans la base de données
                if db_instance.user_exists(username):
                    self.ids.error_label.text = "Nom d'utilisateur déjà utilisé!"
                    return
            if username=="":
                self.ids.error_label.text = "Champ de nom d'utilisateur vide !"
                return

            if email != previous_email:
                #Vérifie si l'adresse e-mail est valide
                if not db_instance.is_valid_email(email):
                    self.ids.error_label.text = "Adresse e-mail invalide"
                    return

                # Vérifie si l'adresse e-mail existe déjà
                if db_instance.email_exists(email):
                    self.ids.error_label.text = "L'adresse mail existe déjà!"
                    return
            if email=="":
                self.ids.error_label.text = "Champ d'adresse mail vide !"
                return
            # Vérifier si le champ de mot de passe est vide ou non
            if password:
                # Vérifie si le mot de passe est valide
                if not db_instance.validate_password(password):
                    self.ids.error_label.text = "Mot de passe invalide (doit contenir au moins 6 caractères)"
                    return
                db_instance.update_user_info(user_id, username, email, salaire,dépencesfixes, password)
            if salaire == 0:
                self.ids.error_label.text = "Le salaire  ne peut pas être égal à zéro."
                self.ids.salaire_input.text = ""
                return
            if dépencesfixes == 0:
                self.ids.error_label.text = "Les dépencesfixes ne peuvent pas être égaux à zéro."
                self.ids.dépences_fixes_input.text = ""
                return

            if previous_salaire!=salaire:
                differences1=salaire - previous_salaire
                dépences_primaires += differences1 * 0.5
                dépences_secondaires += differences1 * 0.3
                investissement += differences1 * 0.2
                db_instance.update_user_expenses(user_id, dépences_primaires , dépences_secondaires, investissement)

            if previous_dépencesfixes!=dépencesfixes:
                differences2=previous_dépencesfixes-dépencesfixes
                dépences_primaires += differences2 * 0.5
                dépences_secondaires += differences2 * 0.3
                investissement += differences2 * 0.2
                db_instance.update_user_expenses(user_id, dépences_primaires , dépences_secondaires, investissement)

            # Si le champ de mot de passe est vide, ne mettez pas à jour le mot de passe dans la base de données
            db_instance.update_user_info_without_password(user_id, username, email, salaire,dépencesfixes)

        self.ids.error_label.text = ""
        # Effacer le champs de mot de passe
        self.ids.password_input.text = ""

class Dépences_courantesScreen(Screen):

    def check_inputs_and_buttons(self):
        description = self.ids.déscription_input.text.strip()
        montant = self.ids.montant_input.text.strip()
        button1_color = self.ids.button1.md_bg_color
        button2_color = self.ids.button2.md_bg_color
        user_id = App.get_running_app().user_id
        db_instance = App.get_running_app().db
        try:
            # Convertir les valeurs en float
            montant = float(montant)
        except ValueError:
            self.ids.error_label.text = "La valeur doit être un chiffre."
            self.ids.montant_input.text = ""
            return

        if not description :
            self.ids.error_label.text = "Remplissez tous les champs."
            self.ids.déscription_input.text=""
            return
        elif not montant:
            self.ids.error_label.text = "Remplissez tous les champs."
            self.ids.montant_input.text=""
            return
        elif montant ==0:
            self.ids.error_label.text = "Le montant ne peut pas etre égal à 0."
            return
        elif button1_color != [0, 1, 0, 1] and button2_color != [0, 1, 0, 1]:
            self.ids.error_label.text = "Sélectionnez un type de dépenses."
            return
        elif button1_color == [0, 1, 0, 1] and button2_color == [0, 1, 0, 1]:
            self.ids.error_label.text = "Sélectionnez un seul type de dépenses."
        else:
            # Récupérer l'épargne actuelle de l'utilisateur
            dépences_primaires, dépences_secondaires, investissement = db_instance.get_user_expenses(user_id)
            if button1_color == [0, 1, 0, 1]:
                if float(montant) > dépences_primaires:
                    self.ids.error_label.text = "Vous etre hors budget"
                    return
                self.record_transaction_primaires()
                self.ids.error_label.text = "Transaction fait avec succé"
                return
            elif button2_color == [0, 1, 0, 1]:
                if float(montant) > dépences_secondaires:
                    self.ids.error_label.text = "Vous etre hors budget"
                    return
                self.record_transaction_secondaires()
                self.ids.error_label.text = "Transaction fait avec succé"
                return

    def record_transaction_primaires(self):
        # Récupérer la description et le montant de la dépense nécessaire depuis les TextInput
        description = self.ids.déscription_input.text
        montant = self.ids.montant_input.text

        # Vérifier si les champs sont vides
        if not description or not montant:
            return  # Si l'un des champs est vide, ne rien faire

        # Convertir le montant en float
        montant = float(montant)

        # Enregistrer la transaction dans la base de données
        user_id = App.get_running_app().user_id
        if user_id:
            db_instance = App.get_running_app().db
            d = datetime.now()
            dt =datetime(year=d.year, month=d.month, day=d.day,
                         hour=d.hour, minute=d.minute)
            db_instance.record_transaction(user_id, "primaires", description, montant,dt )
            # Répartir le montant dans les dépenses utilisateur
            db_instance.allocate_expenses(user_id, montant)

            # Effacer les champs de saisie après l'enregistrement de la transaction
            self.ids.déscription_input.text = ""
            self.ids.montant_input.text = ""

    def record_transaction_secondaires(self):
        # Récupérer la description et le montant de l'épargne depuis les TextInput
        description = self.ids.déscription_input.text
        montant = self.ids.montant_input.text

        # Vérifier si les champs sont vides
        if not description or not montant:
            return  # Si l'un des champs est vide, ne rien faire

        # Convertir le montant en float
        montant = float(montant)

        # Enregistrer la transaction dans la base de données
        user_id = App.get_running_app().user_id
        d = datetime.now()
        dt = datetime(year=d.year, month=d.month, day=d.day,
                      hour=d.hour, minute=d.minute)
        if user_id:
            db_instance = App.get_running_app().db
            db_instance.record_transaction(user_id,"secondaires", description, montant, dt)
            # Soustraire le montant de l'épargne dans les dépenses utilisateur
            db_instance.subtract_from_savings(user_id, montant)

            # Effacer les champs de saisie après l'enregistrement de la transaction
            self.ids.déscription_input.text = ""
            self.ids.montant_input.text = ""

class TransactionScreen(Screen):

    def load_transactions(self):
        user_id = App.get_running_app().user_id
        if user_id:
            db_instance = App.get_running_app().db
            transactions = db_instance.get_user_transactions(user_id)
            # Effacez d'abord les widgets précédents de la liste des transactions
            self.ids.transactions_list.clear_widgets()
            if transactions:
                self.ids.transactions_list.add_widget(Widget())
                sep=" "*6
                line="-"*180
                Type = "Type"
                Catégorie = "Catégorie"
                Montant = "montant"
                Date = "Date"
                for transaction in transactions:
                    transaction_info = f"{Type:5s}:{transaction[0]:10s}{sep} {Catégorie:10s}:{transaction[1]}{sep} {Montant:10s}:{transaction[2]} dt{sep} {Date:5s}:{transaction[3]} "
                    line_info=f"{line}\n{line}\n"
                    label1 = Label(text=line_info, color=(0.345, 0.635, 0.42, 1))
                    label2 = Label(text=transaction_info, color=(0, 0, 0, 1))
                    self.ids.transactions_list.add_widget(label1)
                    self.ids.transactions_list.add_widget(label2)
                    # Ajouter un espace vertical entre chaque transaction
                    self.ids.transactions_list.add_widget(Widget())
            else:
                # Gérer le cas où aucun transaction n'est trouvé
                self.ids.transactions_list.add_widget(Label(text="Aucune transaction trouvée"))
        else:
            # Gérer le cas où aucun utilisateur n'est connecté
            self.ids.transactions_list.add_widget(Label(text="Aucun utilisateur connecté"))
        return

class CalendrierScreen(Screen):
    calendar_text = StringProperty("")  # Property to hold the generated calendar text

    def on_enter(self):
        # Appeler la méthode pour générer le calendrier lorsque l'écran est affiché
        self.generate_calendar()

    def reveal_menu_buttons(self):
        # Obtenir le gestionnaire d'écrans
        screen_manager = self.manager

        # Obtenir la référence à MenuScreen
        menu_screen = screen_manager.get_screen('Menu')

        # Appeler la méthode pour révéler les boutons du menu
        menu_screen.reveal_buttons()

    def generate_calendar(self):
        dt = datetime.now()
        year = dt.year
        month_num = dt.month
        # Generate the calendar for the given year and month
        cal = calendar.TextCalendar(calendar.SUNDAY)
        calendar_str = cal.formatmonth(year, month_num)
        # Convert the calendar to a string
        calendar_str = "\n".join(calendar_str.split('\n')[1:])  # Remove the header
        # Update the calendar_text property
        self.calendar_text = calendar_str

class SuiviScreen(Screen):
    def calcule_sommes(self):
        user_id=App.get_running_app().user_id
        somme_dépences_nes=0.0
        somme_dépences_sec=0.0
        if user_id:
            user_info = App.get_running_app().db.get_user_info_by_id(user_id)
            montant_brut=float(user_info['salaire'])-float(user_info['dépencesfixes'])
            primaires=montant_brut*0.5
            secondaires = montant_brut * 0.3
            self.ids.dépenses_nécessaires_progress.max = primaires
            self.ids.épargne_progress.max = secondaires
            db_instance = App.get_running_app().db
            transactions = db_instance.get_user_transactions(user_id)
            if transactions:
                for transaction in transactions:
                    if transaction[0]=="primaires":
                        somme_dépences_nes+=float(transaction[2])
                    else:
                        somme_dépences_sec+=float(transaction[2])
            self.ids.dépenses_nécessaires_progress.value = somme_dépences_nes
            self.ids.épargne_progress.value = somme_dépences_sec
            self.ids.dépenses_nécessaires_label.text = f"{somme_dépences_nes}dt/{str(primaires)}dt"
            self.ids.épargne_label.text =f"{somme_dépences_sec}dt/{str(secondaires)}dt"
            if self.ids.dépenses_nécessaires_progress.value / self.ids.dépenses_nécessaires_progress.max > 0.75:
                self.ids.dépenses_nécessaires_label.color = (1, 0, 0, 1)  # Rouge
            else:
                self.ids.dépenses_nécessaires_label.color = (0.345, 0.635, 0.42, 1)  # Vert
            if self.ids.épargne_progress.value / self.ids.épargne_progress.max > 0.75:
                self.ids.épargne_label.color = (1, 0, 0, 1)  # Rouge
            else:
                self.ids.épargne_label.color = (0.345, 0.635, 0.42, 1)  # Vert)



class FormationScreen(Screen):
    pass



class TestApp(MDApp):
    def build(self):
        # Applique la couleur blanche sur tous les backgrounds
        Window.clearcolor = (1, 1, 1, 1)
        # Créer une instance de la classe Database
        self.db = Database()

        # Charge les fichiers KV pour chaque écran
        Builder.load_file('introductionscreen.kv')
        Builder.load_file('homescreen.kv')
        Builder.load_file('menuscreen.kv')
        Builder.load_file('settingsscreen.kv')
        Builder.load_file('Incription.kv')
        Builder.load_file('connection.kv')
        Builder.load_file('profil.kv')
        Builder.load_file('salaire_dépencesfixes.kv')
        Builder.load_file('répartitionbudgétaire.kv')
        Builder.load_file('dépences_courantes.kv')
        Builder.load_file('transaction.kv')
        Builder.load_file('feedback.kv')
        Builder.load_file('suivi.kv')
        Builder.load_file('formation.kv')
        Builder.load_file('calendrier.kv')


        # Crée le gestionnaire d'écrans
        sm = ScreenManager()
        sm.add_widget(IntroductionScreen(name='Introduction'))
        sm.add_widget(Homescreen(name='Home'))
        sm.add_widget(MenuScreen(name='Menu'))
        sm.add_widget(SettingsScreen(name='Settings'))
        sm.add_widget(Incriptionscreen(name='Incription'))
        sm.add_widget(ConnectionScreen(name='Connection'))
        sm.add_widget(ProfilScreen(name='Profil'))
        sm.add_widget(SalaireDépencesFixesScreen(name='SalaireDépencesFixes'))
        sm.add_widget(RépartitionBudgétaireScreen(name='RépartitionBudgétaire'))
        sm.add_widget(Dépences_courantesScreen(name='Dépences_courantes'))
        sm.add_widget(TransactionScreen(name='Transaction'))
        sm.add_widget(FeedbackScreen(name='Feedback'))
        sm.add_widget(SuiviScreen(name='Suivi'))
        sm.add_widget(FormationScreen(name='Formation'))
        sm.add_widget(CalendrierScreen(name='Calendrier'))
        return sm



if __name__ == '__main__':
    TestApp().run()
