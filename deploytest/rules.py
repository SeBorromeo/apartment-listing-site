import rules

# predicates
p_is_admin = rules.is_group_member("Administrator")


@rules.predicate
def p_is_listing_author(user, listing):
    return user == listing.author


@rules.predicate
def p_is_listing_approved(_, listing):
    return listing.is_approved


@rules.predicate
def p_is_listing_hidden(_, listing):
    return listing.is_hidden


# register globally-visible rules
rules.set_rule("is_admin", p_is_admin)
