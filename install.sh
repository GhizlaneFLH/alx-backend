#!/bin/bash

echo "🚀 Installation du Système Multi-Agent de Matching CV-Offres"
echo "============================================================"

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

echo "✅ Python3 détecté: $(python3 --version)"

# Installer les dépendances de base
echo "📦 Installation des dépendances..."
pip3 install --break-system-packages -r requirements_simple.txt

# Tenter d'installer spaCy et scikit-learn si possible
echo "🔬 Installation des dépendances ML (optionnelles)..."
pip3 install --break-system-packages scikit-learn --no-deps 2>/dev/null || echo "⚠️  scikit-learn non installé (optionnel)"

# Créer les dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p uploads results static templates

# Rendre le script exécutable
chmod +x test_system.py

echo "✅ Installation terminée !"
echo ""
echo "🧪 Pour tester le système :"
echo "   python3 test_system.py"
echo ""
echo "🚀 Pour démarrer l'application :"
echo "   python3 app.py"
echo ""
echo "🌐 Interface web : http://localhost:5000"