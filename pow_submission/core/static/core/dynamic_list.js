$('select').change(categoryWarning() );

function categoryWarning() {
    var showDisclaimer = false;
    for (let i = 0; i < 5 ; i++) {
      var element = document.getElementById("id_plannedWork_" + i );
      var categoryElement = document.getElementById("id_category_" + i);
      var value = element.value;
      console.log(value);
      if (value == "") {
          categoryElement.style.color = 'black';
      } else {
        var selectedCategory = document.getElementById("id_category_" + i).value;
        var defaultCategoryElement = document.getElementById("table_" + value);
        if (defaultCategoryElement != null) {
          var defaultCategory = defaultCategoryElement.innerText;
          if (selectedCategory == parseInt(defaultCategory)) {
            categoryElement.style.color = 'black';
          } else { 
            categoryElement.style.color = 'red';
            showDisclaimer = true;
          }
        } else {
          categoryElement.style.color = 'red';
        }
      }
    }
    if (showDisclaimer) {

    } else {

    }
}

$('.blankOffering').on('change', function() {
    console.log('hello')
    let $parent = $(this).parent()
    let $clone = $parent.clone()
    let $cloneElement = $clone.children('select').eq(0)
    let name = $cloneElement.attr('name')
    let n = parseInt(name.split('_')[2]) + 1
    name = 'plannedWork_offering_' + n
    $cloneElement.val('')
    $cloneElement.attr('name', name)
    $clone.appendTo($parent.parent())
    $element = $parent.children('select').eq(0)
    $element.removeClass('blankOffering')
    $element.off('change', arguments.callee)
    $cloneElement.on('change', arguments.callee)
    $element.on('blur', hideElement) 
})

$(document).find('select[name^=plannedWork_offering_]:not(.blankOffering)').on('blur', hideElement)

function hideElement() {
    console.log('hide')
    console.log($(this).attr('name'))
    var value = $(this).val();
    if (value === ''){
        $(this).hide();
    }
}

$(window).on('load', function() {
    console.log('load')
    categoryWarning()
    $("input[type='checkbox']").each( function() {
        console.log('load each')
        $(this).closest("tr").find("select[name^='offering']").prop("disabled", !this.checked)
    })
});

$("input[type='checkbox']").on('change', function() {
    console.log('checkbox')
    $(this).closest("tr").find("select[name^='offering']").prop("disabled", !this.checked)
});
