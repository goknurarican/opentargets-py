"""GraphQL queries for target (gene) entities."""

TARGET_QUERY = """
query TargetInfo($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    approvedName
    biotype
    functionDescriptions
    description: proteinAnnotations {
      functions
    }
  }
}
"""

TARGET_ASSOCIATIONS_QUERY = """
query TargetAssociations($ensemblId: String!, $index: Int!, $size: Int!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    associatedDiseases(page: { index: $index, size: $size }) {
      count
      rows {
        disease {
          id
          name
        }
        score
        datasourceScores {
          id
          score
        }
      }
    }
  }
}
"""

TARGET_DRUGS_QUERY = """
query TargetDrugs($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    knownDrugs {
      count
      rows {
        drug {
          id
          name
          drugType
          maximumClinicalTrialPhase
          synonyms
          tradeNames
          mechanismOfAction
        }
      }
    }
  }
}
"""

TARGETS_BATCH_QUERY = """
query TargetsBatch($ids: [String!]!) {
  targets(ensemblIds: $ids) {
    id
    approvedSymbol
    approvedName
    biotype
    functionDescriptions
  }
}
"""
