# Fix: Portal Authorization Error (403 Forbidden)

## Problem
When portal users logged in, they received:
```
403: Forbidden - Doesn't have 'read' access to User (res.users)
```

## Root Cause
Portal users lacked permissions to access the `res.users` model, which is required during portal route rendering.

## Solutions Applied

### 1. Added Portal User Access to res.users Model
**Status**: ✅ Applied via SQL

```sql
INSERT INTO ir_model_access (name, model_id, group_id, perm_read, perm_write, perm_create, perm_unlink)
SELECT 'Portal Users', im.id, 10, true, false, false, false
FROM ir_model im WHERE im.model = 'res.users';
```

- Group 10 = base.group_portal
- Read-only access (perm_read=true, others=false)

### 2. Fixed Portal Controller Document Search
**Status**: ✅ Fixed in `/controllers/portal.py`

**Before** (Line 135-139):
```python
documents = request.env['soya.contract.document'].search([
    '|',
    ('contract_id.owner_id', '=', partner.id),  # WRONG: owner_id doesn't exist
    ('contract_id.tenant_id', '=', partner.id)  # WRONG: tenant_id is on rental contract
], order='upload_date desc')
```

**After**:
```python
documents = request.env['soya.contract.document'].search([
    ('contract_id.landlord_id', '=', partner.id)  # CORRECT: landlord_id exists
], order='upload_date desc')
```

**Reason**: 
- soya_contract_document references soya_base_contract via contract_id
- soya_base_contract has `landlord_id` (not `owner_id`)
- Tenant documents need a more complex search (future enhancement)

### 3. Server Restart
**Status**: ✅ Completed

The server was restarted to load the new access rules.

## Testing the Fix

### Step 1: Clear Browser Cache
- Press `Ctrl+Shift+Delete` (or `Cmd+Shift+Delete` on Mac)
- Clear all browsing data
- Close all browser tabs

### Step 2: Log In as Property Owner

```
URL: http://localhost:8069
Login: proprietaire
Password: proprietaire123
```

**Expected**: You should see the home page WITHOUT the 403 error

### Step 3: Navigate to Property Dashboard
- Click on "My Properties" or navigate to: `http://localhost:8069/my/properties`

**Expected**: You should see the property "Appartement 3 Chambres - Badalabougou Portal"

### Step 4: View Property Details
- Click on the property name

**Expected**: You should see:
- Current tenant: Marie Martin
- Rental income: 750,000 XOF/month
- Associated documents

## If Still Getting 403 Error

### Option 1: Check Browser Cache
- Hard refresh: `Ctrl+F5` (or `Cmd+Shift+R` on Mac)
- Or use Incognito/Private mode

### Option 2: Clear Odoo Session
```bash
docker compose exec redis redis-cli FLUSHALL
docker compose restart web
```

### Option 3: Verify Access Rules in Database
```bash
docker compose exec db psql -U odoo -d soya_odoo_db << 'SQL'
SELECT ima.id, im.model, (rg.name->>'en_US') as group_name, ima.perm_read
FROM ir_model_access ima
JOIN ir_model im ON ima.model_id = im.id
JOIN res_groups rg ON ima.group_id = rg.id
WHERE rg.id = 10 AND im.model IN ('res.users', 'soya.property', 'soya.rental.contract');
SQL
```

Should show portal read access to at least:
- res.users ✓
- soya.property ✓
- soya.rental.contract ✓

### Option 4: Check Odoo Logs
```bash
docker compose logs web | grep -i "access\|permission\|forbidden" | tail -20
```

## Files Modified

| File | Change |
|------|--------|
| `controllers/portal.py` | Fixed document search query (line 135-137) |
| Database | Added portal user access to res.users |

## Current Limitations

**Tenants cannot see documents yet** because:
- The current implementation only searches for landlord documents
- Tenant documents require checking if tenant is in related rental contracts
- This is a future enhancement (Phase 2)

**Workaround for Tenants**: 
- Staff can manually assign documents to tenant via Odoo backoffice
- Or tenants can access `/my/rentals` to see rental-specific documents

## Next Steps

1. Test with both proprietaire and locataire accounts
2. If both work, the portal is ready for use
3. If tenant portal still has issues, additional permission rules may be needed
4. Document any remaining edge cases for future refinement

## References

- Access Control: `/security/ir.model.access.csv`
- Portal Routes: `/controllers/portal.py`
- Portal Templates: `/views/portal_templates.xml`
