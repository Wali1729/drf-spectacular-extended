from drf_spectacular_extended.extensions import OpenApiAuthenticationExtension
from drf_spectacular_extended.plumbing import build_bearer_security_scheme_object


class KnoxTokenScheme(OpenApiAuthenticationExtension):
    target_class = 'knox.auth.TokenAuthentication'
    name = 'knoxApiToken'

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name='Authorization',
            token_prefix=self.target.authenticate_header(""),
        )
