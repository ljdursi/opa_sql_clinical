package filtering

# one
allow = true {
  input.method = "GET"
  input.path = ["individuals", iid]
  allowed[x]
  data.individuals[x].id = iid
}

# list
allow = true {
  input.method = "GET"
  input.path = ["individuals"]
  allowed[x]
}

allowed[x] {
  data.consents[x].project = input.consent
  data.consents[x].consent = true
  data.individuals[x].id = data.consents[x].id 
}
