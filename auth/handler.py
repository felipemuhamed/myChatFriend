from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security, HTTPException
from jose import jwt

KEYCLOAK_PUBLIC_KEY = "-----BEGIN PUBLIC KEY-----\nSUA_CHAVE_AQUI\n-----END PUBLIC KEY-----"
security = HTTPBearer()

class AuthHandler:
    """Classe responsável por validar a identidade do usuário"""
    @staticmethod
    def get_usuario_logado(credentials: HTTPAuthorizationCredentials = Security(security)):
        try:
            payload = jwt.decode(credentials.credentials, KEYCLOAK_PUBLIC_KEY, algorithms=["RS256"], audience="account")
            return payload.get("sub") 
        except Exception:
            raise HTTPException(status_code=401, detail="Token Keycloak inválido ou expirado")