from transactions import User


def test_user_generates_keys():
    bob = User()
    id = bob.getId()
    print(id)
