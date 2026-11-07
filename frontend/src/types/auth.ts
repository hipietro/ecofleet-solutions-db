/**
 * File overview
 * Purpose: Describe authenticated account data used by the customer interface.
 * Responsibilities: Mirror the profile response, including string-serialized credit amounts
 *   and payment-method presence.
 * Connections: Matches backend/app/schemas/auth.py; Profile uses this contract when reading
 *   GET /api/auth/me.
 */

//---profile contract: match the authenticated account response.---
export interface UserProfile{
    codicefiscale: string
    email: string
    ruolo: string
    saldo_crediti: string //its a string because the backend serializes Decimal values like this
    has_payment_method: boolean
}