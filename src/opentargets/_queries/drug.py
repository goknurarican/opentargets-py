"""GraphQL queries for drug entities."""

DRUG_QUERY = """
query DrugInfo($chemblId: String!) {
  drug(chemblId: $chemblId) {
    id
    name
    drugType
    maximumClinicalStage
    synonyms
    tradeNames
    mechanismsOfAction {
      rows {
        mechanismOfAction
      }
    }
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
        maxClinicalStage
        disease {
          id
          name
        }
      }
    }
  }
}
"""

DRUG_CHEMBL_IDS_QUERY = """
query DrugChemblIds($chemblId: String!) {
  drug(chemblId: $chemblId) {
    id
    name
    crossReferences {
      source
      ids
    }
  }
}
"""
