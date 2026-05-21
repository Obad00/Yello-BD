# Dashboard KPI — Yello

## KPI du cahier des charges

| KPI | Source de données | Calcul |
|-----|-------------------|--------|
| Leads générés | Airtable Contacts | COUNT tous statuts |
| Leads qualifiés | Airtable | COUNT où Statut ∈ {Qualifié, Contacté, ...} |
| RDV pris | Airtable | COUNT Statut ∈ {RDV proposé, RDV confirmé} |
| Propositions envoyées | Airtable | COUNT Statut = Proposition envoyée |
| Clients convertis | Airtable | COUNT Statut = Converti |
| Taux de conversion | Calculé | Convertis / Leads générés × 100 |
| Sources performantes | Airtable | GROUP BY Source |
| Taux ouverture newsletter | Brevo | Rapport campagne |
| Taux clic newsletter | Brevo | Rapport campagne |
| Réponses campagnes | Brevo + CRM | Sync manuel ou n8n |
| Revenus générés | Airtable (champ à ajouter) | SUM Montant deal |
| Valeur pipeline | Airtable | SUM deals en Négociation |

## Option A — Airtable Interface (recommandé, rapide)

1. Ouvrez votre base → **Interfaces** → Nouvelle interface
2. Ajoutez des blocs :
   - **Number** : Total contacts (`COUNT(Contacts)`)
   - **Number** : Leads chauds (filtre Score ≥ 61)
   - **Chart** : Contacts par Source (bar chart)
   - **Chart** : Pipeline par Statut commercial (bar)
   - **Grid** : Top 10 priorités (tri Score ↓)

## Option B — Looker Studio

1. Connecteur **Airtable** ou export CSV périodique via n8n
2. Créez un rapport avec :
   - Scorecard : Leads générés, Convertis, Taux conversion
   - Série temporelle : Leads par semaine (Date de création)
   - Table : Performance par Source
3. Connecteur **Brevo** pour métriques newsletter

### Requête conceptuelle (export Airtable → Sheets)

Champs à exporter pour Looker :
- Date de création, Source, Segment, Statut commercial, Score du lead

## Option C — Metabase (stack avancée)

Si migration PostgreSQL :
```sql
SELECT source, COUNT(*) as leads,
       SUM(CASE WHEN statut = 'Converti' THEN 1 ELSE 0 END) as convertis
FROM contacts
GROUP BY source;
```

## Mise à jour automatique du score newsletter

Workflow n8n suggéré :
1. Webhook Brevo (email opened / clicked)
2. Recherche contact Airtable par email
3. Mise à jour Score (+5 ouverture, +10 clic)
4. Recalcul classification

## Validation CDC (critère 6)

Le dashboard est **fonctionnel** quand l'équipe peut voir en un coup d'œil :
- Combien de leads cette semaine
- Combien de RDV
- Quelle source performe le mieux
- Évolution du taux de conversion
