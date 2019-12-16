package filtering

## access list for projects that don't have a DAC
access_list = {"alice":["tf4cn_member"],
               "bob":  ["tf4cn_member"]}

# get the user (subject) from the identity token
idtoken := {"payload": payload} { io.jwt.decode(input.user, [_, payload, _]) }
subject := idtoken.payload.sub

# get set of all entitlements from tokens and access list
claim_entitlements := { name | name = input.entitlements[i].name;
                               [ct_head, ct_payload, ct_sig] = io.jwt.decode(input.entitlements[i].jwt);
                               ct_payload[name] == true }                            
access_list_entitlements := { item | access_list[subject][_] = item }
entitlements := union({claim_entitlements, access_list_entitlements})

default valid_tokens = false
default valid_id_token = false
default valid_entitlement_tokens = false
default allow = false

# authorization is denied if the any token is expired or if signature fails validation
# or if entitlement (DAC claim) token doesn't match ID token
# this is also where we'd check that the issuer is one of
# our trusted federation partners, etc.
valid_id_token = true {
  [id_valid, id_header, id_payload] := io.jwt.decode_verify(input.user, {"secret": "secret"})
  id_valid == true
} 

# if there are no entitlement tokens, they are valid (there's no invalid ones)
valid_entitlement_tokens = true {
	count(input.entitlements) == 0
}

valid_entitlement_tokens = true {
  # if any of the claims tokens are expired or fail signature validation
  # or the subject isn't the same as the ID subject
  # then we fail
  entitlement_checks := [{"valid":valid, "payload":payload} |
                          [valid, header, payload] := io.jwt.decode_verify(input.entitlements[_].jwt, {"secret": "secret"})]
  all([entitlement_checks[_].valid == true])
  all([entitlement_checks[_].payload.sub == subject])
}

valid_tokens {
	valid_id_token
  valid_entitlement_tokens
}

# authorize a single item
# for a single item we can just be given the consents and make the authorization decision
allow = true {
  input.method = "GET"
  input.path = ["individuals", iid]

  any({input.consents[i] == entitlements[j]})
}

# authorize items from a list
allow = true {
  input.method = "GET"
  input.path = ["individuals"]
  
  some x
  row_allowed[x]
}

row_allowed[x] = true {
  data.individuals[x].id = data.consents[x].id 
  data.consents[x].consent = true
  proj := data.consents[x].project

  input.entitlements[i].name == proj
  [_, payload, _] := io.jwt.decode(input.entitlements[i].jwt)
  payload[proj] == true
}

# Alternateily, item is allowed if the data consent matches an entitlement in access list above
row_allowed[x] = true {
  data.individuals[x].id = data.consents[x].id 
  data.consents[x].consent = true
  some j
  data.consents[x].project = access_list[subject][j]
}