find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_program(CTYPESGEN_PATH ctypesgen REQUIRED)

set(_THIS_MODULE_BASE_DIR "${CMAKE_CURRENT_LIST_DIR}")

function(ctypesgen_json target_name input_header output_filename)
    add_custom_command(OUTPUT "${output_filename}"
        COMMAND ${CTYPESGEN_PATH} --output-language=json --no-macro-warnings 
        "-I $<JOIN:$<TARGET_PROPERTY:${target_name},INCLUDE_DIRECTORIES>, -I >" 
        -L "$<TARGET_FILE_DIR:${target_name}>" -l "$<TARGET_FILE_NAME:${target_name}>" 
        "${input_header}"
        -o "${output_filename}"
        BYPRODUCTS "${output_filename}")
    
    if (NOT TARGET ${target_name}_json)
        add_custom_target(${target_name}_json
            ALL 
            DEPENDS "${output_filename}")
    else()
        set_property(TARGET ${target_name}_json APPEND
            PROPERTY DEPENDS "${output_filename}")
    endif()
endfunction()

function(ctypesgen_bindings target_name input_header output_filename)  
    add_custom_command(OUTPUT "${output_filename}"
        COMMAND ${CTYPESGEN_PATH} --no-macro-warnings 
        "-I $<JOIN:$<TARGET_PROPERTY:${target_name},INCLUDE_DIRECTORIES>, -I >" 
        -L "$<TARGET_FILE_DIR:${target_name}>" -l "$<TARGET_FILE_NAME:${target_name}>" 
        "${input_header}"
        -o "${output_filename}"
        BYPRODUCTS "${output_filename}")

    if (NOT TARGET ${target_name}_bindings)
        add_custom_target(${target_name}_bindings
            ALL 
            DEPENDS "${output_filename}")
    else()
        set_property(TARGET ${target_name}_bindings APPEND
            PROPERTY DEPENDS "${output_filename}")
    endif()
endfunction()

function(ctypes_bindings target_name input_header output_filename)
    ctypesgen_bindings(${target_name} ${input_header} ${output_filename})

    get_filename_component(json_filename_no_ext ${output_filename} NAME_WE)
    set(json_filename ${json_filename_no_ext}.json)
    ctypesgen_json(${target_name} ${input_header} ${json_filename})

    get_filename_component(output_directory ${output_filename} DIRECTORY)
    add_custom_command(OUTPUT ${output_filename}
        COMMAND ${Python3_EXECUTABLE} ${_THIS_MODULE_BASE_DIR}/gen_callbackwrappers.py 
        --bindings ${output_filename} --json ${json_filename}
        APPEND)

    get_filename_component(dest_filename ${output_filename} NAME)
    install(FILES ${output_filename} DESTINATION ${Python3_SITEARCH})
endfunction()