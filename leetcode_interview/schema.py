import graphene
import interview.schema


class Query(interview.schema.Query, graphene.ObjectType):
    # 总的Schema的query入口
    pass


class Mutation(interview.schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
