"""
Ultra-fast lazy router loading system for maximum performance.
Routers are only imported when first accessed, not at startup.
"""
from typing import Dict, Any
import importlib
from functools import lru_cache

class FastRouterLoader:
    """Lazy router loader that dramatically reduces startup time"""
    
    def __init__(self):
        self._router_cache: Dict[str, Any] = {}
        self._router_configs = {
            'auth': ('routers.auth', 'router', ['authentication']),
            'meal_plan_generation': ('routers.meal_plan_generation', 'router', ['meal_plans']),
            'utility': ('routers.utility', 'router', ['utility']),
            'privacy': ('routers.privacy_data', 'router', ['privacy']),
            'test': ('routers.test_endpoints', 'router', ['testing']),
            'admin': ('routers.admin_endpoints', 'router', ['admin']),
            'export': ('routers.export_system', 'router', ['export']),
            'chat': ('routers.chat_system', 'router', ['chat']),
            'user_profile': ('routers.user_profile_system', 'router', ['user']),
            'consumption_analysis': ('routers.consumption_analysis', 'router', ['consumption_analysis']),
            'ai_coach': ('routers.ai_coach_system', 'router', ['ai_coach']),
            'ai_coach_comprehensive': ('routers.ai_coach_comprehensive', 'router', ['ai_coach_comprehensive']),
            'meal_plans': ('routers.meal_plans', 'router', ['meal_plans']),
            'pending_consumption': ('routers.pending_consumption_system', 'router', ['pending_consumption']),
            'pdf_generation': ('routers.pdf_generation_system', 'router', ['pdf_generation']),
            'coaching_insights': ('routers.coaching_insights_system', 'router', ['coaching_insights']),
            'consumption_management': ('routers.consumption_management', 'router', ['consumption_management'])
        }
    
    @lru_cache(maxsize=32)
    def get_router(self, router_name: str):
        """Get router with caching - loads only when needed"""
        if router_name in self._router_cache:
            return self._router_cache[router_name]
        
        if router_name not in self._router_configs:
            raise ValueError(f"Unknown router: {router_name}")
        
        module_path, router_attr, tags = self._router_configs[router_name]
        
        try:
            module = importlib.import_module(module_path)
            router = getattr(module, router_attr)
            self._router_cache[router_name] = (router, tags)
            return router, tags
        except Exception as e:
            print(f"[FAST_ROUTER] Failed to load {router_name}: {e}")
            return None, []
    
    def load_essential_routers(self, app):
        """Load only the most critical routers immediately"""
        essential = ['auth', 'utility']  # Only the absolutely necessary ones
        
        for router_name in essential:
            router, tags = self.get_router(router_name)
            if router:
                app.include_router(router, tags=tags)
    
    def load_remaining_routers(self, app):
        """Load remaining routers - can be called asynchronously"""
        remaining = [name for name in self._router_configs.keys() 
                    if name not in ['auth', 'utility']]
        
        loaded_count = 0
        for router_name in remaining:
            try:
                router, tags = self.get_router(router_name)
                if router:
                    app.include_router(router, tags=tags)
                    loaded_count += 1
            except Exception as e:
                print(f"[FAST_ROUTER] Non-critical error loading {router_name}: {e}")
        
        return loaded_count

# Global instance
router_loader = FastRouterLoader()