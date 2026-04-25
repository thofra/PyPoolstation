import json
import aiohttp
import unittest
import os
import sys

# Ensure pypoolstation is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pypoolstation import Account, Pool, TwoFactorAuthRequiredException, AuthenticationException

class TestRealHardware(unittest.IsolatedAsyncioTestCase):
    """
    Integration tests against the real poolstation.net API.
    Requires tests/../credentials.json with valid credentials.
    """

    async def asyncSetUp(self):
        creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
        try:
            with open(creds_path, 'r') as f:
                self.creds = json.load(f)
        except FileNotFoundError:
            self.skipTest("credentials.json not found. Skipping real hardware integration tests.")
            return
            
        self.username = self.creds.get('username')
        self.password = self.creds.get('password')
        
        if not self.username or not self.password or "your_email" in self.username:
            self.skipTest("Invalid or default credentials in credentials.json. Skipping.")
            
        self.session = aiohttp.ClientSession()

    async def asyncTearDown(self):
        if hasattr(self, 'session'):
            await self.session.close()

    async def test_full_hardware_flow(self):
        account = Account(self.session, username=self.username, password=self.password)
        
        try:
            print(f"\nAttempting primary login for {self.username}...")
            token = await account.login(login_code="")
        except TwoFactorAuthRequiredException:
            print("\n!!! 2FA Validation Triggered !!!")
            print("Poolstation just sent an email with the verification code.")
            
            # Since the API relies on the same session, we prompt interactively here.
            import asyncio
            import os
            
            login_code = os.environ.get("POOLSTATION_2FA_CODE")
            if not login_code:
                login_code = await asyncio.to_thread(input, "Please enter the 2FA code from your email: ")
            
            print(f"Retrying login with 2FA code: '{login_code}'...")
            try:
                token = await account.login(login_code=login_code.strip())
            except AuthenticationException as e:
                self.fail(f"Login failed with newly provided 2FA code: {e}")
        except AuthenticationException as e:
            self.fail(f"Login utterly failed, invalid credential or expired code: {e}")
            
        self.assertIsNotNone(token, "Token should not be None")
        self.assertIsInstance(token, str, "Token should be a string")
        self.assertGreater(len(token), 10, "Token should be reasonably long")
        
        # Test pulling pools
        pools = await Pool.get_all_pools(self.session, account=account)
        self.assertIsInstance(pools, list, "Pools should be a list")
        
        if len(pools) > 0:
            pool = pools[0]
            # Ensure it mapped an ID
            self.assertIsNotNone(pool.id, "Pool should have an ID")
            
            # Test synchronizing device telemetry 
            await pool.sync_info()
            
            # Basic validation that parsing didn't fail
            self.assertIsNotNone(pool.alias, "Pool should have an alias")
            self.assertIsInstance(pool.temperature, (float, type(None)))
            self.assertIsInstance(pool.current_ph, (float, type(None)))
            
            # Validate relays
            self.assertIsInstance(pool.relays, list)
            
            print("\n--- Telemetry Data ---")
            print(f"Temperature:         {pool.temperature} °C")
            print(f"Current pH:          {pool.current_ph}")
            print(f"Target pH:           {pool.target_ph}")
            print(f"Salt Concentration:  {pool.salt_concentration} g/l")
            print(f"Electrolysis:        {getattr(pool, 'percentage_electrolysis', 'N/A')}% (Target: {getattr(pool, 'target_percentage_electrolysis', 'N/A')}%)")
            print(f"ORP:                 {getattr(pool, 'current_orp', 'N/A')} (Target: {getattr(pool, 'target_orp', 'N/A')})")
            print(f"UV Available:        {pool.uv_available} | Enabled: {pool.uv_enabled}")
            
            print(f"\n--- Relays ({len(pool.relays)}) ---")
            for relay in pool.relays:
                self.assertIsNotNone(relay.name)
                self.assertIsInstance(relay.active, bool)
                print(f"  [{relay.id}] {relay.name}: {'ON' if relay.active else 'OFF'}")
                
            print(f"\nReal Hardware Test Successful! Hardware connected: {pool.alias} (ID: {pool.id})")
        else:
            print("\nReal Hardware Test completed, but no pools are attached to this account.")

if __name__ == '__main__':
    unittest.main()
