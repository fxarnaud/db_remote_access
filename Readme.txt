Accès BD à distance après avoir fait un git clone

1 - Creation d'une session() sur la BD via la declaration des variables d'environements dans .env :
	Ce fichier est present dans le gitignore. Le creer si absent apres clone git
	Exemple de modele de .env
	# .env
	DATABASE_USER=***
	DATABASE_PASSWORD=****
	DATABASE_HOST=****
	DATABASE_NAME=****
	DATABASE_URL=mysql+pymysql://****:******@*****:*****/****

2 - Création d'un virtual environment
3 - Il faut malgré tout déclarer les classes de la base pour pouvoir faire des requetes simples => Il faut générer (ou régénerer si MAJ des talbes de la BD) models.py :
	- Dans son venv : pip install sqlacodegen. (sqlacodegen Permet à partir de la connexion à distance à la base de générer un models.py automatiquement)
	- Dans une console powershell faire cd vers le dossier du projet puis .\update_models.ps1
	=>Ce fichier va generer models.py puis le modifier un peu pour :
		- que les classes heritent de base.py et non de declarative_base. 
		- que models_extended.py herite des classes de models.py + classes de utils_mixin.py (Utils_mixin.py permet de declarer des fonctions tres utiles comme .to_dict() qui s'appliquent à toutes les tables de la base)
	
	Au final dans mon main j'utilise donc les tables qui ont été modifées dans mon models_extended.py : from models_extended import * et non from models import *