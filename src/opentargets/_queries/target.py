"""GraphQL queries for target (gene) entities."""

TARGET_QUERY = """
query TargetInfo($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    approvedName
    biotype
    functionDescriptions
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
    drugAndClinicalCandidates {
      count
      rows {
        drug {
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

TARGET_TRACTABILITY_QUERY = """
query TargetTractability($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    tractability {
      modality
      label
      value
    }
  }
}
"""

TARGET_SAFETY_QUERY = """
query TargetSafety($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    safetyLiabilities {
      event
      eventId
      datasource
      literature
      url
      effects {
        direction
        dosing
      }
      biosamples {
        tissueLabel
        tissueId
        cellLabel
        cellId
      }
    }
  }
}
"""

TARGET_EXPRESSION_QUERY = """
query TargetExpression($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    expressions {
      tissue {
        id
        label
      }
      rna {
        value
        level
        zscore
        unit
      }
      protein {
        level
        reliability
      }
    }
  }
}
"""

TARGET_CONSTRAINT_QUERY = """
query TargetConstraint($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    geneticConstraint {
      constraintType
      obs
      exp
      oe
      oeLower
      oeUpper
      score
    }
  }
}
"""

TARGET_DRUGS_WITH_CHEMBL_QUERY = """
query TargetDrugsWithChembl($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    drugAndClinicalCandidates {
      count
      rows {
        drug {
          id
          name
          crossReferences {
            source
            ids
          }
        }
      }
    }
  }
}
"""
