# Real-Time Financial Data Pipeline

## 🎯 Objectif du Projet
Fournir une solution simple et performante pour ingérer, traiter et visualiser des données financières en temps réel, destinée aux traders et analystes.

## 🧩 Technologies Utilisées
- **Finnhub** : Source de données en temps réel
- **Kafka** : Distribution des messages
- **Spark Streaming** : Traitement temps réel
- **Cassandra** : Stockage rapide
- **Grafana** : Dashboards interactifs
- **Kubernetes & Terraform** : Déploiement et orchestration

## 🔄 Étapes du Pipeline
1. **Source de Données** : Récupération en direct via WebSocket depuis Finnhub
2. **Kafka** : Envoi des données via un producteur personnalisé
3. **Spark** : Nettoyage + agrégations toutes les 5 secondes
4. **Cassandra** : Stockage structuré pour interrogation rapide
5. **Grafana** : Visualisation dynamique des métriques

## ⚙️ Déploiement
Déploiement de tous les composants sur Kubernetes avec provisionnement via Terraform.

## 🔐 Sécurité
Variables sensibles et clés d’API stockées dans des fichiers `.env`

## 📈 Améliorations Futures
- Ajout de modèles prédictifs pour anticiper les fluctuations des prix des actifs financiers.
- Amélioration de la gestion des erreurs pour des scénarios de panne plus complexes.
- Extension du pipeline à d'autres sources de données financières.

## 👤 Auteur du Projet
- **Nom** : Ali Rahiqi
- **Email** : ali123rahiqi@gmail.com

---

