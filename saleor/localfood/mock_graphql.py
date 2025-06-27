"""
Mock GraphQL components for local development.
"""
import graphene
from graphene import relay


class MockLocalFoodError(graphene.ObjectType):
    """Mock error type for LocalFood operations."""
    field = graphene.String()
    message = graphene.String()
    code = graphene.String()


class MockConnection:
    """Mock GraphQL connection for pagination."""
    
    @staticmethod
    def create_connection_slice(queryset, info, kwargs, node_type):
        """Mock connection slice creation."""
        # Simple implementation for development
        edges = []
        for item in queryset[:10]:  # Limit to 10 items for development
            edges.append({
                'node': item,
                'cursor': str(item.id)
            })
        
        return {
            'edges': edges,
            'page_info': {
                'has_next_page': False,
                'has_previous_page': False,
                'start_cursor': edges[0]['cursor'] if edges else None,
                'end_cursor': edges[-1]['cursor'] if edges else None,
            }
        }


def mock_get_node_from_global_id(info, global_id, node_type):
    """Mock node resolution for development."""
    # Extract ID from global ID (simplified)
    try:
        _, node_id = global_id.split(':')
        return node_type.objects.get(id=node_id)
    except:
        return None


def mock_from_global_id_or_error(global_id, node_type):
    """Mock global ID resolution."""
    try:
        type_name, node_id = global_id.split(':')
        return type_name, node_id
    except:
        raise Exception(f"Invalid global ID: {global_id}")


class MockBaseMutation(graphene.Mutation):
    """Mock base mutation for development."""
    
    @classmethod
    def get_node_or_error(cls, info, node_id, only_type=None):
        """Mock node retrieval."""
        try:
            type_name, pk = mock_from_global_id_or_error(node_id, only_type)
            # Simple mock - would need proper implementation for full functionality
            return {"id": pk, "type": type_name}
        except:
            raise Exception(f"Node not found: {node_id}")
    
    @classmethod
    def success_response(cls, instance):
        """Mock success response."""
        return cls(errors=[], **{cls._meta.return_field_name: instance})