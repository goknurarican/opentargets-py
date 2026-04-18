"""GraphQL queries for drug entities."""

DRUG_QUERY = """
query DrugInfo($chemblId: String!) {
  drug(chemblId: $chemblId) {
    id
    name
    drugType
    mechanismOfAction
    synonyms
    tradeNames
    maximumClinicalTrialPhase
  }
}
"""

DRUG_INDICATIONS_QUERY = """
query DrugIndications($chemblId: String!) {
  drug(chemblId: $chemblId) {
    id
    name
    indications {
      count
      rows {
        maxPhaseForIndication
        disease {
          id
          name
        }
      }
    }
  }
}
"""
