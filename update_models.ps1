# Charger les variables depuis le fichier .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#=]+?)\s*=\s*(.+?)\s*$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($key, $value)
    }
}

# Lire les variables d'environnement
$DB_USER     = $env:DATABASE_USER
$DB_PASS     = $env:DATABASE_PASSWORD
$DB_HOST     = $env:DATABASE_HOST
$DB_NAME     = $env:DATABASE_NAME

# Afficher les variables chargées
Write-Host "DATABASE_USER     = $DB_USER"
Write-Host "DATABASE_PASSWORD = $DB_PASS"
Write-Host "DATABASE_HOST     = $DB_HOST"
Write-Host "DATABASE_NAME     = $DB_NAME"

# Construire l'URL de connexion
$env:DATABASE_URL = "mysql+pymysql://$DB_USER`:$DB_PASS@$DB_HOST/$DB_NAME"

# Exécuter sqlacodegen avec python -m pour générer models.py
env_connexion_bd\Scripts\python.exe -m sqlacodegen $env:DATABASE_URL --outfile models.py

# Charger les lignes du fichier
$lines = Get-Content models.py

# Créer une nouvelle liste pour le fichier corrigé
$modifiedLines = New-Object System.Collections.Generic.List[string]

$foundBaseDeclaration = $false

foreach ($line in $lines) {
    if ($line -match "^\s*from sqlalchemy\.orm import DeclarativeBase, Mapped, mapped_column, relationship") {
        $modifiedLines.Add("#" + $line)
        $modifiedLines.Add("from sqlalchemy.orm import Mapped, mapped_column, relationship")
        $modifiedLines.Add("from base import Base")
    }
    elseif ($line -match "^\s*class Base\(DeclarativeBase\):") {
        $modifiedLines.Add("#" + $line)
        $foundBaseDeclaration = $true
    }
    elseif ($foundBaseDeclaration -and ($line -match "^\s*pass\s*$")) {
        $modifiedLines.Add("#" + $line)
        $foundBaseDeclaration = $false
    }
    else {
        $modifiedLines.Add($line)
    }
}

# Écrire le résultat modifié
$modifiedLines | Set-Content models.py

Write-Host "models.py modifié avec succès."
