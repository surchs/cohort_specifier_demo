from query import create_query


def test_basic_smoke_test():
    # Setup
    age_range = (10, 20)
    gender = 'male'
    diagnosis = 'Parkinson'
    image = 'T1'
    # Run
    result = create_query(age=age_range, gender=gender, diagnosis=diagnosis, image=image)
    # Test
    assert '?age' in result
    assert '?gender' in result
    assert '?diagnosis' in result
    assert '?image' in result