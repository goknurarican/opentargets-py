"""GraphQL queries for target–disease association entities."""

ASSOCIATION_QUERY = """
query Association($ensemblId: String!, $efoId: String!) {
  associationByDatatypes(ensemblId: $ensemblId, efoId: $efoId) {
    target {
      id
      approvedSymbol
    }
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
"""
