"""GraphQL queries for disease entities."""

DISEASE_QUERY = """
query DiseaseInfo($efoId: String!) {
  disease(efoId: $efoId) {
    id
    name
    description
    therapeuticAreas {
      id
      name
    }
    dbXRefs
  }
}
"""

DISEASE_TARGETS_QUERY = """
query DiseaseTargets($efoId: String!, $index: Int!, $size: Int!) {
  disease(efoId: $efoId) {
    id
    name
    associatedTargets(page: { index: $index, size: $size }) {
      count
      rows {
        target {
          id
          approvedSymbol
          approvedName
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
