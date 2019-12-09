package filtering

## access list for proejcts that don't have a DAC
access_list = {"alice":["tf4cn_member"],
               "bob":  ["tf4cn_member"]}

# authorization is denied if the identity token is expired
# or if signature fails validation
# this is also where we'd check that the issuer is one of
# our trusted federation partners, etc.
allow = false {
  [valid, header, payload] := io.jwt.decode_verify(input.user, {"secret": "secret"})
  valid == false
}

# if any of the claims tokens are expired or fail signature validation
# then we also fail
allow = false {
  [valid, header, payload] := io.jwt.decode_verify(input.entitlements[_].jwt, {"secret": "secret"})
  valid == false
}

# get the user (subject) from the identity token
# we'd actually use issuer:subject as the key rather than just subject
idtoken := {"payload": payload} { io.jwt.decode(input.user, [_, payload, _]) }
subject := idtoken.payload.sub

# authorize a single item
allow = true {
  input.method = "GET"
  input.path = ["individuals", iid]
  some x
  row_allowed[x]
  data.individuals[x].id = iid
}

# authorize items from a list
allow = true {
  input.method = "GET"
  input.path = ["individuals"]
  some x
  row_allowed[x]
}

# Item is allowed if the input entitlement (e.g. from a DAC) matches the data consent...
row_allowed[x] {
  data.individuals[x].id = data.consents[x].id 
  data.consents[x].consent = true
  proj := data.consents[x].project
  some i
  input.entitlements[i].name == proj
  [_, payload, _] := io.jwt.decode(input.entitlements[i].jwt)
  payload[proj] == true
}

# Alternateily, item is allowed if the data consent matches an entitlement in access list above
row_allowed[x] {
  some j
  data.individuals[x].id = data.consents[x].id 
  data.consents[x].consent = true
  data.consents[x].project = access_list[subject][j]
}