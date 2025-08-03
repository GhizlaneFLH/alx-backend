from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import logging
import uuid
from werkzeug.utils import secure_filename
import tempfile
import shutil
from datetime import datetime

from agents import CoordinatorAgent

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'

# Créer les dossiers nécessaires
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Extensions de fichiers autorisées
ALLOWED_EXTENSIONS = {'pdf'}

# Instance globale du coordinateur
coordinator = CoordinatorAgent()

# Sessions actives (en production, utiliser Redis ou une base de données)
active_sessions = {}

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, prefix=""):
    """Sauvegarde un fichier uploadé et retourne le chemin"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{prefix}_{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        return filepath
    return None

@app.route('/')
def index():
    """Page d'accueil avec l'interface utilisateur"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de vérification de l'état de l'API"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api/upload-offer', methods=['POST'])
def upload_offer():
    """Upload d'une offre d'emploi PDF"""
    try:
        if 'offer' not in request.files:
            return jsonify({"error": "Aucun fichier d'offre fourni"}), 400
        
        file = request.files['offer']
        if file.filename == '':
            return jsonify({"error": "Aucun fichier sélectionné"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Type de fichier non autorisé. Utilisez PDF uniquement"}), 400
        
        # Sauvegarder le fichier
        filepath = save_uploaded_file(file, "offer")
        if not filepath:
            return jsonify({"error": "Erreur lors de la sauvegarde du fichier"}), 500
        
        # Créer une session
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            "offer_path": filepath,
            "cv_paths": [],
            "created_at": datetime.now().isoformat(),
            "status": "offer_uploaded"
        }
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Offre d'emploi uploadée avec succès",
            "filename": file.filename
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de l'upload de l'offre: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route('/api/upload-cvs', methods=['POST'])
def upload_cvs():
    """Upload de plusieurs CVs PDF"""
    try:
        session_id = request.form.get('session_id')
        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Session invalide"}), 400
        
        if 'cvs' not in request.files:
            return jsonify({"error": "Aucun fichier CV fourni"}), 400
        
        files = request.files.getlist('cvs')
        if not files or all(f.filename == '' for f in files):
            return jsonify({"error": "Aucun fichier CV sélectionné"}), 400
        
        saved_files = []
        failed_files = []
        
        for file in files:
            if file and file.filename != '':
                if allowed_file(file.filename):
                    filepath = save_uploaded_file(file, "cv")
                    if filepath:
                        saved_files.append({
                            "original_name": file.filename,
                            "path": filepath
                        })
                    else:
                        failed_files.append(file.filename)
                else:
                    failed_files.append(f"{file.filename} (type non autorisé)")
        
        if not saved_files:
            return jsonify({"error": "Aucun CV valide uploadé"}), 400
        
        # Mettre à jour la session
        active_sessions[session_id]["cv_paths"] = [f["path"] for f in saved_files]
        active_sessions[session_id]["cv_files"] = saved_files
        active_sessions[session_id]["status"] = "cvs_uploaded"
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": f"{len(saved_files)} CVs uploadés avec succès",
            "uploaded_files": [f["original_name"] for f in saved_files],
            "failed_files": failed_files
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de l'upload des CVs: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route('/api/process-matching', methods=['POST'])
def process_matching():
    """Lance le processus de matching"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Session invalide"}), 400
        
        session_data = active_sessions[session_id]
        
        if session_data["status"] != "cvs_uploaded":
            return jsonify({"error": "Upload des fichiers incomplet"}), 400
        
        # Vérifier que les fichiers existent toujours
        if not os.path.exists(session_data["offer_path"]):
            return jsonify({"error": "Fichier offre non trouvé"}), 400
        
        for cv_path in session_data["cv_paths"]:
            if not os.path.exists(cv_path):
                return jsonify({"error": f"Fichier CV non trouvé: {cv_path}"}), 400
        
        # Lancer le traitement
        session_data["status"] = "processing"
        
        result = coordinator.process_matching_request(
            offer_pdf_path=session_data["offer_path"],
            cv_pdf_paths=session_data["cv_paths"],
            session_id=session_id
        )
        
        if result["success"]:
            session_data["status"] = "completed"
            session_data["results"] = result
        else:
            session_data["status"] = "failed"
            session_data["error"] = result
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Erreur lors du traitement: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route('/api/results/<session_id>', methods=['GET'])
def get_results(session_id):
    """Récupère les résultats d'une session"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Session non trouvée"}), 404
        
        session_data = active_sessions[session_id]
        
        if session_data["status"] != "completed":
            return jsonify({
                "status": session_data["status"],
                "message": "Traitement en cours ou échoué"
            })
        
        # Type de résultat demandé
        result_type = request.args.get('type', 'summary')
        
        if result_type == 'detailed':
            results = coordinator.get_detailed_results()
        else:
            results = coordinator.get_results_summary()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "results": results
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des résultats: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route('/api/candidate/<session_id>/<cv_id>', methods=['GET'])
def get_candidate_detail(session_id, cv_id):
    """Récupère les détails d'un candidat spécifique"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Session non trouvée"}), 404
        
        session_data = active_sessions[session_id]
        
        if session_data["status"] != "completed":
            return jsonify({"error": "Traitement non terminé"}), 400
        
        candidate_detail = coordinator.get_candidate_detail(cv_id)
        
        if not candidate_detail:
            return jsonify({"error": "Candidat non trouvé"}), 404
        
        return jsonify({
            "success": True,
            "candidate": candidate_detail
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération du détail candidat: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route('/api/export/<session_id>', methods=['GET'])
def export_results(session_id):
    """Exporte les résultats en CSV"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Session non trouvée"}), 404
        
        session_data = active_sessions[session_id]
        
        if session_data["status"] != "completed":
            return jsonify({"error": "Traitement non terminé"}), 400
        
        # Créer le fichier CSV
        export_filename = f"matching_results_{session_id[:8]}.csv"
        export_path = os.path.join(app.config['RESULTS_FOLDER'], export_filename)
        
        success = coordinator.export_results_to_csv(export_path)
        
        if not success:
            return jsonify({"error": "Erreur lors de l'export"}), 500
        
        return send_file(
            export_path,
            as_attachment=True,
            download_name=export_filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        logging.error(f"Erreur lors de l'export: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """Liste toutes les sessions actives"""
    try:
        sessions = []
        for session_id, data in active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "status": data["status"],
                "created_at": data["created_at"],
                "offer_file": os.path.basename(data.get("offer_path", "")),
                "cv_count": len(data.get("cv_paths", []))
            })
        
        return jsonify({
            "success": True,
            "sessions": sessions
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de la liste des sessions: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Supprime une session et ses fichiers"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Session non trouvée"}), 404
        
        session_data = active_sessions[session_id]
        
        # Supprimer les fichiers uploadés
        try:
            if os.path.exists(session_data["offer_path"]):
                os.remove(session_data["offer_path"])
            
            for cv_path in session_data.get("cv_paths", []):
                if os.path.exists(cv_path):
                    os.remove(cv_path)
        except Exception as e:
            logging.warning(f"Erreur lors de la suppression des fichiers: {e}")
        
        # Supprimer la session
        del active_sessions[session_id]
        
        return jsonify({
            "success": True,
            "message": "Session supprimée avec succès"
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de la suppression de session: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.errorhandler(413)
def too_large(e):
    """Gestionnaire pour les fichiers trop volumineux"""
    return jsonify({"error": "Fichier trop volumineux (max 50MB)"}), 413

@app.errorhandler(404)
def not_found(e):
    """Gestionnaire pour les pages non trouvées"""
    return jsonify({"error": "Endpoint non trouvé"}), 404

@app.errorhandler(500)
def internal_error(e):
    """Gestionnaire pour les erreurs internes"""
    return jsonify({"error": "Erreur interne du serveur"}), 500

def cleanup_old_files():
    """Nettoie les anciens fichiers (à exécuter périodiquement)"""
    try:
        current_time = datetime.now()
        
        # Supprimer les sessions de plus de 24h
        expired_sessions = []
        for session_id, data in active_sessions.items():
            created_at = datetime.fromisoformat(data["created_at"])
            if (current_time - created_at).total_seconds() > 86400:  # 24h
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            try:
                # Supprimer les fichiers
                session_data = active_sessions[session_id]
                if os.path.exists(session_data["offer_path"]):
                    os.remove(session_data["offer_path"])
                
                for cv_path in session_data.get("cv_paths", []):
                    if os.path.exists(cv_path):
                        os.remove(cv_path)
                
                del active_sessions[session_id]
                logging.info(f"Session expirée supprimée: {session_id}")
            except Exception as e:
                logging.error(f"Erreur lors du nettoyage de session {session_id}: {e}")
        
    except Exception as e:
        logging.error(f"Erreur lors du nettoyage: {e}")

if __name__ == '__main__':
    # Nettoyer les anciens fichiers au démarrage
    cleanup_old_files()
    
    # Lancer l'application
    app.run(host='0.0.0.0', port=5000, debug=True)