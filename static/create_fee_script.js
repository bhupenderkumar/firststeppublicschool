$(document).ready(function() {
    // Get the list of all students from the backend
    $.get("/students", function(data) {
        // Create an autocomplete object for the student name input field
        var autocomplete = new google.maps.places.Autocomplete(
            document.getElementById("student_name"),
            {
                types: ["establishment"],
                countries: ["IN"],
            }
        );

        // Bind the autocomplete object to the data from the backend
        autocomplete.setPlaces(data);

        // When the user selects a student from the autocomplete list,
        // update the hidden student ID input field with the student's ID
        autocomplete.addListener("place_changed", function() {
            var place = autocomplete.getPlace();
            $("#student_id").val(place.id);
        });
    });
});