import graphene
import humeur.schema
import notification.schema
import nutrition.schema  
from mcp_engine.schema import Query as McpQueryEngine

class Query(
    McpQueryEngine,
    humeur.schema.Query,
    notification.schema.Query,
    nutrition.schema.Query, 
    graphene.ObjectType
):
    pass

class Mutation(
    humeur.schema.Mutation,
    nutrition.schema.Mutation,  
    graphene.ObjectType
):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)